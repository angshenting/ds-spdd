"""Canvas O step 5: evaluate the selected model on the test split, once per round.

Safeguard test_set_single_use: every test evaluation is a line in
experiments/test_results.jsonl, and this script refuses to run if the selected
model's round already has one.
"""

import json
import sys

import joblib
from common import (
    EXPERIMENTS,
    GUARDRAIL,
    GUARDRAIL_TARGET,
    MODELS,
    PRIMARY,
    PRIMARY_TARGET,
    load_split,
    score,
)

RESULTS = EXPERIMENTS / "test_results.jsonl"


def main() -> int:
    selection = json.loads((MODELS / "selected_model.json").read_text())
    earlier = []
    if RESULTS.exists():
        earlier = [json.loads(line) for line in RESULTS.read_text().splitlines() if line]
    if any(r["round"] == selection["round"] for r in earlier):
        print(f"round {selection['round']} already used the test split; see {RESULTS.name}")
        return 1
    model = joblib.load(MODELS / "selected_model.joblib")
    x_test, y_test = load_split("test")
    metrics = score(y_test, model.predict(x_test))
    targets = {PRIMARY: PRIMARY_TARGET, GUARDRAIL: GUARDRAIL_TARGET}
    result = {
        "round": selection["round"],
        "run_id": selection["run_id"],
        "evaluated_on": "test",
        "n_test": len(y_test),
        "metrics": metrics,
        "targets": {name: {"op": ">=", "value": value} for name, value in targets.items()},
        "met": {name: metrics[name] >= value for name, value in targets.items()},
    }
    lines = [json.dumps(r, sort_keys=True) for r in [*earlier, result]]
    RESULTS.write_text("\n".join(lines) + "\n")
    print(f"round {selection['round']} test ({len(y_test)} rows), {selection['run_id']}: {metrics}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
