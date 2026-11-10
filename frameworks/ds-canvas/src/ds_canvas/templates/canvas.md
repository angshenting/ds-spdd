---
name: REPLACE-with-project-name
---

# REASONS Canvas — REPLACE-with-project-name

## R — Requirements

REPLACE: business goal — the decision this model supports and why it matters.

### Success criteria

REPLACE: what must be true for the project to be done, tied to the metrics below.

```yaml
key_metrics: []
```

## E — Entities (Data Definitions)

```yaml
datasets:
  - name: REPLACE-dataset-name
    source: REPLACE-path-or-query
    grain: REPLACE-one-row-per-what
    fields:
      # type: string | integer | float | boolean | datetime
      # role (optional): key | feature | target; unit (optional): free text
      - name: REPLACE-field-name
        type: string
        role: key
      - name: REPLACE-target-field
        type: integer
        role: target
      - name: REPLACE-derived-field
        type: float
        derived_from: [REPLACE-input-fields]
    # optional — name a set of fields once, then use the name in any
    # `fields` list (quality rules, S ops, pii_fields):
    # field_groups:
    #   REPLACE-group-name: [REPLACE-field-name]
    quality_rules:
      # unique | non_negative: fields only
      # missing_at_most: max (ratio 0-1); allowed_values: values (list)
      # range: min and/or max
      - rule: unique
        fields: [REPLACE-field-name]
```

## A — Approach

REPLACE: framing — why this task type and these metrics.

```yaml
task: binary_classification
target: REPLACE-target-field
split:
  method: temporal
  column: REPLACE-time-or-group-column
  ratios:
    train: 0.7
    validation: 0.15
    test: 0.15
metrics:
  primary:
    name: REPLACE-primary-metric
    direction: maximize
    target:
      op: ">="
      value: 0.0
  guardrails: []
model_families:
  - name: REPLACE-baseline-family
    role: baseline
  - name: REPLACE-candidate-family
    role: candidate
    # optional bounded search — declare the budget BEFORE tuning; the
    # validator enforces method (grid|random), a positive integer budget,
    # and for grid that the budget covers the full declared space:
    # search:
    #   method: grid
    #   budget: REPLACE-trials-covering-the-space
    #   space:
    #     REPLACE-param: [REPLACE-values]
# optional calibration — changes threshold semantics, so it is contract:
# calibration:
#   method: REPLACE-sigmoid-or-isotonic
#   fit_on: train
```

## S — Structure (Pipeline)

```yaml
cleaning:
  - op: deduplicate
    fields: [REPLACE-key-fields]
  - op: derive
    fields: [REPLACE-input-fields]
    fn: REPLACE-product-ratio-log1p-indicator
    output: REPLACE-derived-field
  - op: aggregate
    fields: [REPLACE-source-field]
    group_by: [REPLACE-group-key]
    lookback: REPLACE-prior-rows
    fn: REPLACE-sum-mean-min-max-count
    output: REPLACE-derived-field
preprocessing:
  - op: impute_median
    fields: [REPLACE-field-name]
    fit_on: train
  - op: drop
    fields: [REPLACE-target-field]
artifacts:
  models: models/
  reports: reports/
tracking:
  tool: file
  location: experiments/
```

Cleaning ops run before the split and must be stateless (`deduplicate`,
`coerce_type`, `clip`, `derive`, `aggregate`); anything fitted (`winsorize`,
imputers, encoders, scalers) belongs in `preprocessing` with `fit_on: train`.
`aggregate` windows need the full ordered history, so they live in `cleaning`
(pre-split) only. Preprocessing ops are `drop`, `passthrough`, `derive`,
`impute_mean`, `impute_median`, `impute_constant`, `one_hot_encode`,
`target_encode`, `scale_standard`, `scale_minmax` and `winsorize`; any other
name is an error. The target must be listed in a `drop` op. Derived fields must be declared in E with `derived_from`
provenance — the validator rejects any field whose provenance reaches the
target (transitive leakage) and warns on fields no op produces.

## O — Operations

1. EDA on the train split only — exit: data quality rules in E verified
2. Preprocessing per S — exit: REPLACE-a-check-on-the-code (e.g. every fitted op's statistics computed from train rows only, and logged)
3. Train baseline and candidates on train, select on validation — exit: every run appended to the tracking file with its round
4. Evaluate the selected model on test, once per selection round — exit: the evaluation is recorded with per-class or per-segment metrics; Results updated only if every target is met
5. Write report from Results — exit: report references the canvas

## N — Norms

```yaml
seed: 42
environment:
  manager: uv
  lock: true
```

## S — Safeguards

```yaml
target_excluded_from_features: true
test_set_single_use: true
split_before_fit: true
pii_fields: []
```
