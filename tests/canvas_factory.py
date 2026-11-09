VALID_CANVAS = """\
---
name: churn-prediction
---

# REASONS Canvas — churn-prediction

## R — Requirements

Reduce involuntary churn by predicting which subscription customers will
cancel within 30 days, so the retention team can target interventions.

### Success criteria

The retention team can act on the top decile with acceptable precision.
The project is done when the selected model meets the metric targets below
on the test split, once.

```yaml
key_metrics:
  - recall_at_30
```

## E — Entities (Data Definitions)

```yaml
datasets:
  - name: subscriptions
    source: data/raw/subscriptions.csv
    grain: one row per customer per month
    fields:
      - name: customer_id
        type: string
        role: key
      - name: month
        type: string
      - name: monthly_charges
        type: float
        unit: USD
      - name: plan_type
        type: string
      - name: churned_next_30d
        type: integer
        role: target
      - name: support_tickets
        type: integer
      - name: charge_log
        type: float
        derived_from: [monthly_charges]
      - name: tickets_3m_mean
        type: float
        derived_from: [customer_id, month, support_tickets]
    quality_rules:
      - rule: unique
        fields: [customer_id, month]
      - rule: non_negative
        fields: [monthly_charges]
      - rule: missing_at_most
        fields: [monthly_charges]
        max: 0.05
      - rule: allowed_values
        fields: [plan_type]
        values: [basic, standard, premium]
```

## A — Approach

Frame as binary classification at customer grain: predict churn in the next
30 days. Logistic regression baseline for interpretability; gradient
boosting as the main candidate family.

```yaml
task: binary_classification
target: churned_next_30d
split:
  method: temporal
  column: month
  ratios:
    train: 0.7
    validation: 0.15
    test: 0.15
metrics:
  primary:
    name: recall_at_30
    direction: maximize
    target:
      op: ">="
      value: 0.65
  guardrails:
    - name: precision_at_30
      direction: maximize
      target:
        op: ">="
        value: 0.2
model_families:
  - name: logistic_regression
    role: baseline
  - name: gradient_boosting
    role: candidate
    search:
      method: grid
      budget: 4
      space:
        learning_rate: [0.05, 0.1]
        max_leaf_nodes: [31, 63]
calibration:
  method: sigmoid
  fit_on: train
```

## S — Structure (Pipeline)

Preprocessing fits on train only. Features come from the declared fields
plus plan_type interactions.

```yaml
cleaning:
  - op: deduplicate
    fields: [customer_id, month]
  - op: clip
    fields: [monthly_charges]
    min: 0
  - op: derive
    fields: [monthly_charges]
    fn: log1p
    output: charge_log
  - op: aggregate
    fields: [support_tickets]
    group_by: [customer_id]
    lookback: 3
    fn: mean
    output: tickets_3m_mean
preprocessing:
  - op: impute_median
    fields: [monthly_charges]
    fit_on: train
  - op: one_hot_encode
    fields: [plan_type]
    fit_on: train
  - op: drop
    fields: [churned_next_30d]
artifacts:
  models: models/
  reports: reports/
tracking:
  tool: file
  location: experiments/
```

## O — Operations

1. EDA on the train split only — exit: data quality rules in E verified
2. Preprocessing per S — exit: transformed data round-trips to field list
3. Train baseline and candidates on train, select on validation — exit:
   models tracked
4. Evaluate the selected model on test, once — exit: Results updated
5. Write report from Results — exit: report references the canvas

## N — Norms

All experiments must be reproducible and tracked.

```yaml
seed: 42
environment:
  manager: uv
  lock: true
```

## S — Safeguards

The contract below is non-negotiable; violating any item invalidates the run.

```yaml
target_excluded_from_features: true
test_set_single_use: true
split_before_fit: true
pii_fields: []
```
"""


def valid_canvas() -> str:
    return VALID_CANVAS


RESULTS_SECTION = """
## Results

Evaluated the selected gradient boosting model on the test split, once.

```yaml
results:
  - metric: recall_at_30
    achieved: 0.68
  - metric: precision_at_30
    achieved: 0.24
```
"""


def valid_canvas_with_results() -> str:
    return valid_canvas() + RESULTS_SECTION


def with_section_yaml(canvas: str, heading: str, block: str) -> str:
    import re

    pattern = re.compile(r"(" + re.escape(heading) + r"\n[\s\S]*?```yaml\n)([\s\S]*?)(\n```)")
    assert pattern.search(canvas), f"heading not found: {heading}"
    return pattern.sub(lambda m: m.group(1) + block + m.group(3), canvas, count=1)
