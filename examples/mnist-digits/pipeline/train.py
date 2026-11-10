"""Canvas O steps 3-4: fit baseline and candidates on train, select on validation.

Features are the 64 unscaled pixels; `image_id` and `digit` never enter (S `drop`, the
only op). Every run is tracked in experiments/runs.jsonl with its round; re-running a
round replaces that round's lines and keeps every other round.
"""

import json
import sys
from typing import Any

import joblib
from common import (
    EXPERIMENTS,
    GUARDRAIL,
    GUARDRAIL_TARGET,
    MODELS,
    PREPROCESSING,
    PRIMARY,
    ROUND,
    SEED,
    load_split,
    score,
)
from sklearn.base import ClassifierMixin
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

RUNS = EXPERIMENTS / "runs.jsonl"
FAMILIES: list[tuple[str, str, ClassifierMixin]] = [
    ("logistic_regression", "baseline", LogisticRegression(max_iter=2000, random_state=SEED)),
    ("svm_rbf", "candidate", SVC(kernel="rbf", random_state=SEED)),
    ("knn", "candidate", KNeighborsClassifier()),
]


def run(family: str, role: str, estimator: ClassifierMixin) -> tuple[dict[str, Any], Any]:
    x_train, y_train = load_split("train")
    x_validation, y_validation = load_split("validation")
    model = estimator.fit(x_train, y_train)
    record = {
        "round": ROUND,
        "run_id": f"r{ROUND}-{family}",
        "family": family,
        "role": role,
        "preprocessing": PREPROCESSING,
        "params": {k: v for k, v in estimator.get_params().items() if v is not None},
        "seed": SEED,
        "fit_on": "train",
        "evaluated_on": "validation",
        "metrics": score(y_validation, model.predict(x_validation)),
    }
    return record, model


def write_log(records: list[dict[str, Any]]) -> None:
    earlier = []
    if RUNS.exists():
        earlier = [json.loads(line) for line in RUNS.read_text().splitlines() if line]
    kept = [r for r in earlier if r["round"] != ROUND]
    lines = [json.dumps(r, sort_keys=True) for r in kept + records]
    EXPERIMENTS.mkdir(parents=True, exist_ok=True)
    RUNS.write_text("\n".join(lines) + "\n")


def main() -> int:
    results = [run(family, role, estimator) for family, role, estimator in FAMILIES]
    write_log([record for record, _ in results])
    for record, _ in results:
        print(f"{record['run_id']:24} {record['metrics']}")
    eligible = [(r, m) for r, m in results if r["metrics"][GUARDRAIL] >= GUARDRAIL_TARGET]
    if not eligible:
        print(f"no round-{ROUND} run meets the {GUARDRAIL} guardrail on validation")
        return 1
    best, model = max(eligible, key=lambda pair: pair[0]["metrics"][PRIMARY])
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODELS / "selected_model.joblib", compress=3)
    selection = {
        "round": ROUND,
        "run_id": best["run_id"],
        "rule": f"max validation {PRIMARY} among runs with {GUARDRAIL} >= {GUARDRAIL_TARGET}",
        "validation_metrics": best["metrics"],
    }
    (MODELS / "selected_model.json").write_text(json.dumps(selection, indent=2) + "\n")
    print(f"round {ROUND}: selected {best['run_id']} on validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
