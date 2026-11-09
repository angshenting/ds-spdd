"""O step 6: evaluate the selected model on the test split, exactly once.

Writes experiments/test_result.json. No tuning happens here — test is used
once per model selection round (Safeguards: test_set_single_use).
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
from train import METRICS_THRESHOLD, load

DEMO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = DEMO_ROOT / "experiments"
MODELS = DEMO_ROOT / "models"
TARGET = "churned_next_30d"


def main() -> None:
    model = joblib.load(MODELS / "selected_model.joblib")
    selected = json.loads((MODELS / "selected_model.json").read_text())

    X_test, y_test = load("test")
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= METRICS_THRESHOLD).astype(int)
    tp = int(((pred == 1) & (y_test == 1)).sum())
    fp = int(((pred == 1) & (y_test == 0)).sum())
    fn = int(((pred == 0) & (y_test == 1)).sum())
    recall = tp / (tp + fn)
    precision = tp / (tp + fp)

    result = {
        "family": selected["family"],
        "seed": selected["seed"],
        "threshold": METRICS_THRESHOLD,
        "split": "test",
        "recall_at_30": round(recall, 4),
        "precision_at_30": round(precision, 4),
        "ts": datetime.now(UTC).isoformat(),
    }
    (EXPERIMENTS / "test_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
