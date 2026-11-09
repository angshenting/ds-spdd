---
name: churn-demo
---

# REASONS Canvas — churn-demo

## R — Requirements

Predict which subscription customers will cancel within 30 days, so the
retention team can target intervention offers at high-likelihood churners
each month. The project is done when the selected model meets the metric
targets below on the test split, once, and the report traces every claim
back to this canvas.

### Success criteria

The retention team can act on model-flagged customers with acceptable
precision and recall. The model is reviewed monthly against the targets
below before the team acts.

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
        description: "YYYY-MM; temporal split ordering column, not a feature"
      - name: monthly_charges
        type: float
        unit: USD
      - name: plan_type
        type: string
      - name: tenure_months
        type: integer
      - name: support_tickets
        type: integer
      - name: churned_next_30d
        type: integer
        role: target
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
        values: [standard, premium]
```

The raw extract is known to carry upstream defects (about 0.4% duplicated
rows and a handful of negative charges); the S cleaning ops below are the
contract-level fixes for both.

## A — Approach

Binary classification at customer-month grain: predict churn within the
next 30 days. Logistic regression baseline for interpretability; gradient
boosting as the main candidate. Recall is primary (catch likely churners);
precision has a floor so the offer budget is not wasted. Thresholds are
fixed in the metric definition to keep evaluation deterministic.

The candidate declares a bounded grid search (class-imbalance handling via
positive-class weighting): the operating point at the fixed 0.4 threshold
leans conservative, and precision has headroom over its guardrail. Trials
run on validation only, within the declared budget.

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
    params:
      threshold: 0.4
    target:
      op: ">="
      value: 0.6
  guardrails:
    - name: precision_at_30
      direction: maximize
      params:
        threshold: 0.4
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
        pos_weight: [1, 2, 4, 8]
```

## S — Structure (Pipeline)

Preprocessing fits on train only; the fitted values (median, categories) are
applied unchanged to validation and test. The target, the key, and the split
column are dropped from features.

```yaml
cleaning:
  - op: deduplicate
    fields: [customer_id, month]
  - op: clip
    fields: [monthly_charges]
    min: 0
preprocessing:
  - op: impute_median
    fields: [monthly_charges]
    fit_on: train
  - op: one_hot_encode
    fields: [plan_type]
    fit_on: train
  - op: scale_standard
    fields: [tenure_months]
    fit_on: train
  - op: drop
    fields: [churned_next_30d, customer_id, month]
artifacts:
  processed: data/processed/
  models: models/
  reports: reports/
tracking:
  tool: file
  location: experiments/
```

## O — Operations

1. Generate synthetic subscriptions data — exit: data/raw/subscriptions.csv
   exists with the E schema (raw extract includes known defects)
2. Clean per S (deduplicate on customer_id+month; clip monthly_charges at
   0) — exit: no duplicate keys, no negative charges, split ratios intact
3. Split per A (temporal on month) — exit: data/processed/{train,val,test}.csv
   written, row ratios match A
4. Quality gate per E quality_rules on the train split only — exit: all
   rules PASS; the step exits non-zero on the first failure
5. Preprocess per S — exit: fitted values computed from train only and
   logged; processed splits written
6. Train baseline and candidates on train, select on validation — exit: runs
   tracked in experiments/runs.jsonl within the declared search budget,
   winner saved to models/
7. Evaluate the selected model on test, once — exit:
   experiments/test_result.json written
8. Update canvas Results from test_result.json — exit: `ds-canvas validate`
   exits 0
9. Write report.md — exit: every report claim traces to this canvas

## N — Norms

All experiments must be reproducible and tracked. Every run records family,
seed, trial params, and validation metrics; the test split is never used
for tuning. Search trials live within the budget declared in A.

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
pii_fields: [customer_id]
```

## Results

Evaluated the selected gradient boosting model (pos_weight 8, selected on
validation within the declared budget of 4 trials) on the test split, once
for the model-enhancements selection round (2026-11-06).

```yaml
results:
  - metric: recall_at_30
    achieved: 0.9638
  - metric: precision_at_30
    achieved: 0.3339
```
