"""O step 6: train baseline + candidate search on train, select on validation.

Records every trial to experiments/runs.jsonl (N: tracking, seed, trial
params) and saves the selected model to models/. Selection law per the
model-enhancements contract: guardrails filter on validation, the primary
metric orders; trials live within the budget declared in A.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

DEMO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = DEMO_ROOT / "data" / "processed"
EXPERIMENTS = DEMO_ROOT / "experiments"
MODELS = DEMO_ROOT / "models"
SEED = 42
TARGET = "churned_next_30d"
METRICS_THRESHOLD = 0.4
SEARCH_SPACE = {"pos_weight": [1, 2, 4, 8]}
GUARDRAIL_MIN_PRECISION = 0.2


def load(name: str) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(PROCESSED / f"{name}.csv")
    return df.drop(columns=[TARGET]), df[TARGET]


def recall_precision(y_true: pd.Series, proba: pd.Series, threshold: float) -> tuple:
    pred = (proba >= threshold).astype(int)
    tp = int(((pred == 1) & (y_true == 1)).sum())
    fp = int(((pred == 1) & (y_true == 0)).sum())
    fn = int(((pred == 0) & (y_true == 1)).sum())
    recall = tp / (tp + fn) if tp + fn else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    return recall, precision


def trial(family: str, params: dict, model, X_train, y_train, X_val, y_val) -> dict:
    weights = np.where(y_train == 1, params.get("pos_weight", 1), 1) if params else None
    model.fit(X_train, y_train, sample_weight=weights)
    recall, precision = recall_precision(y_val, model.predict_proba(X_val)[:, 1], METRICS_THRESHOLD)
    return {
        "family": family,
        "params": params,
        "seed": SEED,
        "threshold": METRICS_THRESHOLD,
        "split": "validation",
        "recall_at_30": round(recall, 4),
        "precision_at_30": round(precision, 4),
        "ts": datetime.now(UTC).isoformat(),
    }


def main() -> None:
    X_train, y_train = load("train")
    X_val, y_val = load("validation")

    baseline = LogisticRegression(max_iter=1000, random_state=SEED)
    runs = [
        (
            trial("logistic_regression", {}, baseline, X_train, y_train, X_val, y_val),
            baseline,
        )
    ]
    for pos_weight in SEARCH_SPACE["pos_weight"]:
        params = {"pos_weight": pos_weight}
        model = HistGradientBoostingClassifier(random_state=SEED)
        runs.append(
            (
                trial("gradient_boosting", params, model, X_train, y_train, X_val, y_val),
                model,
            )
        )

    EXPERIMENTS.mkdir(exist_ok=True)
    with (EXPERIMENTS / "runs.jsonl").open("a", encoding="utf-8") as fh:
        for run, _ in runs:
            fh.write(json.dumps(run) + "\n")

    eligible = [pair for pair in runs if pair[0]["precision_at_30"] >= GUARDRAIL_MIN_PRECISION]
    winner_run, winner_model = max(eligible, key=lambda pair: pair[0]["recall_at_30"])
    MODELS.mkdir(exist_ok=True)
    joblib.dump(winner_model, MODELS / "selected_model.joblib")
    (MODELS / "selected_model.json").write_text(
        json.dumps(
            {"family": winner_run["family"], "params": winner_run["params"], "seed": SEED},
            indent=2,
        )
    )
    for run, _ in runs:
        print(
            f"{run['family']} {run['params']}: "
            f"val recall_at_30={run['recall_at_30']:.4f} "
            f"precision_at_30={run['precision_at_30']:.4f}"
        )
    print(
        f"selected on validation (guardrail >= {GUARDRAIL_MIN_PRECISION}): "
        f"{winner_run['family']} {winner_run['params']}"
    )


if __name__ == "__main__":
    main()
