---
name: mnist-digits
---

# REASONS Canvas — mnist-digits

## R — Requirements

Read single handwritten digits from scanned form boxes so they no longer need
manual keying (illustrative framing on a public benchmark; see
`ds/analysis.md`). A misread digit costs more than a manual keystroke, so the
model must be accurate overall and must not read any one digit badly.

### Success criteria

On the test split, evaluated once per selection round: accuracy at least
0.97, and recall of the worst-read digit at least 0.90.

```yaml
key_metrics: [accuracy, min_class_recall]
```

## E — Entities (Data Definitions)

```yaml
datasets:
  - name: digits
    source: data/raw/digits.csv (sklearn.datasets.load_digits via data/fetch.py)
    grain: one row per handwritten digit image (8x8 ink-count grid)
    fields:
      - {name: image_id, type: integer, role: key}
      - {name: pixel_0_0, type: integer, unit: ink_count, role: feature}
      - {name: pixel_0_1, type: integer, unit: ink_count, role: feature}
      - {name: pixel_0_2, type: integer, unit: ink_count, role: feature}
      - {name: pixel_0_3, type: integer, unit: ink_count, role: feature}
      - {name: pixel_0_4, type: integer, unit: ink_count, role: feature}
      - {name: pixel_0_5, type: integer, unit: ink_count, role: feature}
      - {name: pixel_0_6, type: integer, unit: ink_count, role: feature}
      - {name: pixel_0_7, type: integer, unit: ink_count, role: feature}
      - {name: pixel_1_0, type: integer, unit: ink_count, role: feature}
      - {name: pixel_1_1, type: integer, unit: ink_count, role: feature}
      - {name: pixel_1_2, type: integer, unit: ink_count, role: feature}
      - {name: pixel_1_3, type: integer, unit: ink_count, role: feature}
      - {name: pixel_1_4, type: integer, unit: ink_count, role: feature}
      - {name: pixel_1_5, type: integer, unit: ink_count, role: feature}
      - {name: pixel_1_6, type: integer, unit: ink_count, role: feature}
      - {name: pixel_1_7, type: integer, unit: ink_count, role: feature}
      - {name: pixel_2_0, type: integer, unit: ink_count, role: feature}
      - {name: pixel_2_1, type: integer, unit: ink_count, role: feature}
      - {name: pixel_2_2, type: integer, unit: ink_count, role: feature}
      - {name: pixel_2_3, type: integer, unit: ink_count, role: feature}
      - {name: pixel_2_4, type: integer, unit: ink_count, role: feature}
      - {name: pixel_2_5, type: integer, unit: ink_count, role: feature}
      - {name: pixel_2_6, type: integer, unit: ink_count, role: feature}
      - {name: pixel_2_7, type: integer, unit: ink_count, role: feature}
      - {name: pixel_3_0, type: integer, unit: ink_count, role: feature}
      - {name: pixel_3_1, type: integer, unit: ink_count, role: feature}
      - {name: pixel_3_2, type: integer, unit: ink_count, role: feature}
      - {name: pixel_3_3, type: integer, unit: ink_count, role: feature}
      - {name: pixel_3_4, type: integer, unit: ink_count, role: feature}
      - {name: pixel_3_5, type: integer, unit: ink_count, role: feature}
      - {name: pixel_3_6, type: integer, unit: ink_count, role: feature}
      - {name: pixel_3_7, type: integer, unit: ink_count, role: feature}
      - {name: pixel_4_0, type: integer, unit: ink_count, role: feature}
      - {name: pixel_4_1, type: integer, unit: ink_count, role: feature}
      - {name: pixel_4_2, type: integer, unit: ink_count, role: feature}
      - {name: pixel_4_3, type: integer, unit: ink_count, role: feature}
      - {name: pixel_4_4, type: integer, unit: ink_count, role: feature}
      - {name: pixel_4_5, type: integer, unit: ink_count, role: feature}
      - {name: pixel_4_6, type: integer, unit: ink_count, role: feature}
      - {name: pixel_4_7, type: integer, unit: ink_count, role: feature}
      - {name: pixel_5_0, type: integer, unit: ink_count, role: feature}
      - {name: pixel_5_1, type: integer, unit: ink_count, role: feature}
      - {name: pixel_5_2, type: integer, unit: ink_count, role: feature}
      - {name: pixel_5_3, type: integer, unit: ink_count, role: feature}
      - {name: pixel_5_4, type: integer, unit: ink_count, role: feature}
      - {name: pixel_5_5, type: integer, unit: ink_count, role: feature}
      - {name: pixel_5_6, type: integer, unit: ink_count, role: feature}
      - {name: pixel_5_7, type: integer, unit: ink_count, role: feature}
      - {name: pixel_6_0, type: integer, unit: ink_count, role: feature}
      - {name: pixel_6_1, type: integer, unit: ink_count, role: feature}
      - {name: pixel_6_2, type: integer, unit: ink_count, role: feature}
      - {name: pixel_6_3, type: integer, unit: ink_count, role: feature}
      - {name: pixel_6_4, type: integer, unit: ink_count, role: feature}
      - {name: pixel_6_5, type: integer, unit: ink_count, role: feature}
      - {name: pixel_6_6, type: integer, unit: ink_count, role: feature}
      - {name: pixel_6_7, type: integer, unit: ink_count, role: feature}
      - {name: pixel_7_0, type: integer, unit: ink_count, role: feature}
      - {name: pixel_7_1, type: integer, unit: ink_count, role: feature}
      - {name: pixel_7_2, type: integer, unit: ink_count, role: feature}
      - {name: pixel_7_3, type: integer, unit: ink_count, role: feature}
      - {name: pixel_7_4, type: integer, unit: ink_count, role: feature}
      - {name: pixel_7_5, type: integer, unit: ink_count, role: feature}
      - {name: pixel_7_6, type: integer, unit: ink_count, role: feature}
      - {name: pixel_7_7, type: integer, unit: ink_count, role: feature}
      - {name: digit, type: integer, role: target}
    field_groups:
      pixels: [
        pixel_0_0, pixel_0_1, pixel_0_2, pixel_0_3, pixel_0_4, pixel_0_5, pixel_0_6, pixel_0_7,
        pixel_1_0, pixel_1_1, pixel_1_2, pixel_1_3, pixel_1_4, pixel_1_5, pixel_1_6, pixel_1_7,
        pixel_2_0, pixel_2_1, pixel_2_2, pixel_2_3, pixel_2_4, pixel_2_5, pixel_2_6, pixel_2_7,
        pixel_3_0, pixel_3_1, pixel_3_2, pixel_3_3, pixel_3_4, pixel_3_5, pixel_3_6, pixel_3_7,
        pixel_4_0, pixel_4_1, pixel_4_2, pixel_4_3, pixel_4_4, pixel_4_5, pixel_4_6, pixel_4_7,
        pixel_5_0, pixel_5_1, pixel_5_2, pixel_5_3, pixel_5_4, pixel_5_5, pixel_5_6, pixel_5_7,
        pixel_6_0, pixel_6_1, pixel_6_2, pixel_6_3, pixel_6_4, pixel_6_5, pixel_6_6, pixel_6_7,
        pixel_7_0, pixel_7_1, pixel_7_2, pixel_7_3, pixel_7_4, pixel_7_5, pixel_7_6, pixel_7_7,
      ]
    quality_rules:
      - rule: unique
        fields: [image_id]
      - rule: missing_at_most
        fields: [image_id, digit]
        max: 0.0
      - rule: allowed_values
        fields: [digit]
        values: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
      - rule: range
        fields: [pixels]
        min: 0
        max: 16
```

## A — Approach

Ten-class classification, because the decision is "which digit is this".
Classes are balanced (174–183 per digit), so accuracy is a fair primary
metric. The guardrail is the recall of the worst-read digit, so a good
average cannot hide one digit that is read badly. There is no time or writer
column, so the split is random, stratified by digit.

```yaml
task: multiclass_classification
target: digit
split:
  method: stratified
  column: digit
  ratios:
    train: 0.7
    validation: 0.15
    test: 0.15
metrics:
  primary:
    name: accuracy
    direction: maximize
    target:
      op: ">="
      value: 0.97
  guardrails:
    - name: min_class_recall
      direction: maximize
      target:
        op: ">="
        value: 0.90
model_families:
  - name: logistic_regression
    role: baseline
  - name: svm_rbf
    role: candidate
  - name: knn
    role: candidate
```

## S — Structure (Pipeline)

```yaml
preprocessing:
  - op: drop
    fields: [image_id, digit]
artifacts:
  models: models/
  reports: reports/
tracking:
  tool: file
  location: experiments/
```

No fitted preprocessing. All 64 pixels share one unit (ink count) and the
0–16 range enforced by E's quality rules. Round 1 used `scale_standard`,
which inflated rare edge pixels to z-scores of up to 35 on train; it was
removed for round 2 (see the round record in `report.md`).

## O — Operations

1. Fetch the raw data with `data/fetch.py` — exit: `data/raw/digits.csv` has 1,797 rows and 66 columns
2. Split per A, then EDA and the E quality rules on the train split only — exit: `pipeline/preprocess.py` exits 0 with every quality rule passing, and writes the three splits to `data/processed/` and `reports/eda.md`
3. Preprocessing per S — exit: `image_id` and `digit` never reach a model's inputs, and the 64 pixels enter unscaled, with no fitted preprocessing stage (checked by review of `pipeline/train.py`)
4. Train the baseline and candidates on train, select on validation — exit: every run is a line in `experiments/runs.jsonl`, and `models/selected_model.json` names the best validation accuracy among runs that meet the guardrail
5. Evaluate the selected model on test, once per selection round — exit: the round's line is appended to `experiments/test_results.jsonl`, and the canvas Results are updated only if every target is met
6. Write the report from Results — exit: `report.md` cites the canvas and states each metric's achieved value and target

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
