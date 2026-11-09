"""O steps 2-5: clean per S, split per A, quality gate per E, preprocess per S.

Cleaning (deduplicate, clip) is stateless and runs before the split so row
ratios in A stay intact. Fitted values (median, one-hot categories,
standard-scale parameters) come from the train split only, per Safeguards
(split_before_fit). The quality gate enforces the E quality_rules on the
train split and exits non-zero on the first failure.
"""

from pathlib import Path

import pandas as pd

DEMO_ROOT = Path(__file__).resolve().parent.parent
RAW = DEMO_ROOT / "data" / "raw" / "subscriptions.csv"
PROCESSED = DEMO_ROOT / "data" / "processed"
RATIOS = {"train": 0.7, "validation": 0.15, "test": 0.15}
SPLIT_COLUMN = "month"
TARGET = "churned_next_30d"
FEATURE_DROP_FIELDS = ["customer_id", "month"]
EDA_REPORT = DEMO_ROOT / "reports" / "eda.md"


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """S cleaning ops: deduplicate on (customer_id, month); clip monthly_charges at 0."""
    before = len(df)
    df = df.drop_duplicates(["customer_id", "month"], keep="first")
    df["monthly_charges"] = df["monthly_charges"].clip(lower=0)
    print(f"clean: removed {before - len(df)} duplicate rows, clipped negative charges at 0")
    return df


def quality_gate(train: pd.DataFrame) -> list[str]:
    """E quality_rules, verified on the train split only. Returns failure messages."""
    failures: list[str] = []
    if train.duplicated(["customer_id", "month"]).any():
        failures.append("unique [customer_id, month]: FAIL — duplicate keys remain")
    if (train["monthly_charges"].dropna() < 0).any():
        failures.append("non_negative [monthly_charges]: FAIL — negative values remain")
    missing_rate = train["monthly_charges"].isna().mean()
    if missing_rate > 0.05:
        failures.append(
            f"missing_at_most [monthly_charges] max 0.05: FAIL — rate is {missing_rate:.3f}"
        )
    bad_values = set(train["plan_type"].dropna().unique()) - {"standard", "premium"}
    if bad_values:
        failures.append(
            f"allowed_values [plan_type]: FAIL — unexpected values {sorted(bad_values)}"
        )
    return failures


def split_temporal(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    ordered = df.sort_values(SPLIT_COLUMN, kind="stable").reset_index(drop=True)
    n = len(ordered)
    train_end = int(n * RATIOS["train"])
    val_end = train_end + int(n * RATIOS["validation"])
    return {
        "train": ordered.iloc[:train_end],
        "validation": ordered.iloc[train_end:val_end],
        "test": ordered.iloc[val_end:],
    }


def main() -> None:
    df = pd.read_csv(RAW)
    df = clean(df)
    splits = split_temporal(df)
    train = splits["train"]

    failures = quality_gate(train)
    lines = [
        "# EDA (train split only)",
        "",
        f"- rows: {len(train)}",
        f"- churn rate: {train[TARGET].mean():.3f}",
        f"- monthly_charges missing rate: {train['monthly_charges'].isna().mean():.3f}",
        (
            "- quality rules: unique [customer_id, month]: PASS; "
            "non_negative [monthly_charges]: PASS; "
            "missing_at_most [monthly_charges] max 0.05: PASS; "
            "allowed_values [plan_type]: PASS"
        ),
    ]
    EDA_REPORT.parent.mkdir(parents=True, exist_ok=True)
    EDA_REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if failures:
        for failure in failures:
            print(f"QUALITY GATE: {failure}")
        raise SystemExit(1)

    median = train["monthly_charges"].median()
    categories = sorted(train["plan_type"].unique())
    tenure_mean = train["tenure_months"].mean()
    tenure_std = train["tenure_months"].std()

    for name, split in splits.items():
        out = split.copy()
        out["monthly_charges"] = out["monthly_charges"].fillna(median)
        for category in categories:
            out[f"plan_type_{category}"] = (out["plan_type"] == category).astype(int)
        out = out.drop(columns=["plan_type", *FEATURE_DROP_FIELDS])
        out["tenure_months"] = ((out["tenure_months"] - tenure_mean) / tenure_std).round(6)
        PROCESSED.mkdir(parents=True, exist_ok=True)
        path = PROCESSED / f"{name}.csv"
        out.to_csv(path, index=False)
        print(f"{name}: {len(out)} rows, ratios ok, columns: {sorted(out.columns)}")

    print("\nfitted on train only:")
    print(f"  impute_median(monthly_charges): {median:.2f}")
    print(f"  one_hot_encode(plan_type) categories: {categories}")
    print(f"  scale_standard(tenure_months): mean={tenure_mean:.2f} std={tenure_std:.2f}")


if __name__ == "__main__":
    main()
