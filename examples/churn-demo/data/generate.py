"""O step 1: generate synthetic subscriptions data per the E section of ds/canvas.md.

Simulates a raw extract with known upstream defects: duplicated rows and
occasional negative charges. These are extract bugs, not model signal —
the canvas S cleaning ops fix them before the split.
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
DEMO_ROOT = Path(__file__).resolve().parent.parent
CUSTOMERS = 3000
MONTHS = [f"2025-{m:02d}" for m in range(1, 11)]
MISSING_CHARGE_RATE = 0.05
DUPLICATE_ROWS = 120
NEGATIVE_ROWS = 50


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def main() -> None:
    rng = np.random.default_rng(SEED)
    customer_ids = [f"C{i:05d}" for i in range(1, CUSTOMERS + 1)]
    plan_std = rng.random(CUSTOMERS) < 0.7

    rows = []
    for i, customer in enumerate(customer_ids):
        for m, month in enumerate(MONTHS):
            tenure = m + 1
            charge = abs(rng.normal(60, 25))
            charge = np.clip(charge, 10.0, 200.0)
            tickets = int(rng.poisson(0.4))
            plan = "standard" if plan_std[i] else "premium"
            logit = (
                -1.3
                + 1.6 * np.tanh((charge - 60.0) / 25.0)
                + 0.8 * tickets
                + 0.4 * float(plan == "standard")
                - 0.5 * min(tenure, 12) / 12.0
            )
            churned = int(rng.random() < sigmoid(logit))
            rows.append(
                {
                    "customer_id": customer,
                    "month": month,
                    "monthly_charges": round(float(charge), 2),
                    "plan_type": plan,
                    "tenure_months": tenure,
                    "support_tickets": tickets,
                    "churned_next_30d": churned,
                }
            )

    df = pd.DataFrame(rows)
    missing = rng.random(len(df)) < MISSING_CHARGE_RATE
    df.loc[missing, "monthly_charges"] = np.nan

    dup_idx = rng.choice(len(df), size=DUPLICATE_ROWS, replace=False)
    df = pd.concat([df, df.iloc[dup_idx]], ignore_index=True)
    present = df["monthly_charges"].dropna().index
    neg_idx = rng.choice(present, size=NEGATIVE_ROWS, replace=False)
    df.loc[neg_idx, "monthly_charges"] = -np.abs(rng.uniform(1, 40, NEGATIVE_ROWS)).round(2)

    out = DEMO_ROOT / "data" / "raw" / "subscriptions.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"wrote {len(df)} rows to {out.relative_to(DEMO_ROOT)}")
    print(f"churn rate: {df['churned_next_30d'].mean():.3f}")
    print(f"missing monthly_charges: {df['monthly_charges'].isna().mean():.3f}")
    print(f"duplicate (customer_id, month) rows: {df.duplicated(['customer_id', 'month']).sum()}")
    print(f"negative monthly_charges rows: {(df['monthly_charges'] < 0).sum()}")


if __name__ == "__main__":
    main()
