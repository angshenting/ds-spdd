"""Canvas O step 2: split per A, quality rules and EDA on train only, write splits.

Canvas S has no fitted ops; its one op, `drop`, is applied where features are selected
(common.load_split returns the 64 pixels only).
"""

import sys

import pandas as pd
from common import ID, PIXELS, PROCESSED, RAW, REPORTS, SEED, SPLITS, TARGET
from sklearn.model_selection import train_test_split

RATIOS = {"train": 0.7, "validation": 0.15, "test": 0.15}
DIGITS = set(range(10))
INK_MIN, INK_MAX = 0, 16


def split(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rest, test = train_test_split(
        frame, test_size=RATIOS["test"], stratify=frame[TARGET], random_state=SEED
    )
    validation_share = RATIOS["validation"] / (RATIOS["train"] + RATIOS["validation"])
    train, validation = train_test_split(
        rest, test_size=validation_share, stratify=rest[TARGET], random_state=SEED
    )
    return {"train": train, "validation": validation, "test": test}


def quality_findings(train: pd.DataFrame) -> list[str]:
    findings = []
    if not train[ID].is_unique:
        findings.append(f"unique: {ID} has {train[ID].duplicated().sum()} duplicates")
    for field in (ID, TARGET):
        missing = train[field].isna().mean()
        if missing > 0.0:
            findings.append(f"missing_at_most: {field} missing ratio {missing:.4f} > 0.0")
    bad_digits = set(train[TARGET].dropna().unique()) - DIGITS
    if bad_digits:
        findings.append(f"allowed_values: {TARGET} has {sorted(bad_digits)}")
    for pixel in PIXELS:
        low, high = train[pixel].min(), train[pixel].max()
        if low < INK_MIN or high > INK_MAX:
            findings.append(f"range: {pixel} spans {low}-{high}, outside {INK_MIN}-{INK_MAX}")
    return findings


def eda_report(splits: dict[str, pd.DataFrame]) -> str:
    train = splits["train"]
    sizes = ", ".join(f"{name} {len(splits[name])}" for name in SPLITS)
    counts = train[TARGET].value_counts().sort_index()
    count_row = " | ".join(str(int(n)) for n in counts)
    mean_ink = train[PIXELS].mean().to_numpy().reshape(8, 8)
    ink_rows = "\n".join("| " + " | ".join(f"{v:.1f}" for v in row) + " |" for row in mean_ink)
    constant = [p for p in PIXELS if train[p].nunique() == 1]
    return f"""# EDA — train split only

Produced by `pipeline/preprocess.py` (canvas O step 2). Validation and test
rows are counted, never inspected.

## Split sizes

{sizes} (stratified by `{TARGET}`, seed {SEED}).

## Class balance (train)

| {" | ".join(str(d) for d in counts.index)} |
|{"---|" * len(counts)}
| {count_row} |

## Mean ink per pixel (train, 0-16 scale)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
|---|---|---|---|---|---|---|---|
{ink_rows}

Pixels constant on train: {", ".join(f"`{p}`" for p in constant) or "none"}. They are
kept: the canvas declares all 64 pixels as features, and a pixel that is the
same in every training image adds nothing to a distance between them.

## Quality rules (canvas E)

All passed on train: `unique` ({ID}), `missing_at_most` 0.0 ({ID}, {TARGET}),
`allowed_values` 0-9 ({TARGET}), `range` {INK_MIN}-{INK_MAX} (all 64 pixels).
"""


def main() -> int:
    frame = pd.read_csv(RAW)
    splits = split(frame)
    findings = quality_findings(splits["train"])
    if findings:
        print("quality rules failed on train:", *findings, sep="\n  ")
        return 1
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for name in SPLITS:
        splits[name].sort_values(ID).to_csv(PROCESSED / f"{name}.csv", index=False)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "eda.md").write_text(eda_report(splits))
    print("quality rules passed on train;", ", ".join(f"{n} {len(splits[n])}" for n in SPLITS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
