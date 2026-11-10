---
name: spec-driven-ds
description: Spec-driven development for data science / ML projects, adapted from
  SPDD (REASONS canvas). Use when starting a new DS/ML project from a business
  goal or dataset, when requirements/data/model choices change mid-project, or
  when an existing DS project needs its design contract reconstructed. Produces a
  validated REASONS canvas, implements the pipeline from it, evaluates once on
  test, reports, and keeps code and canvas in sync.
---

# Spec-driven DS

The canvas is the contract. The pipeline code is an implementation of the
canvas — never the other way round. When reality diverges from the canvas,
**fix the canvas first**, then the code.

The canvas lives in the target project at `ds/canvas.md`. It is a
first-class, version-controlled artifact. Every phase below ends with a
checkable exit condition.

The canvas is validated by the `ds-canvas` framework from this repo
(`frameworks/ds-canvas/`). Its two commands:

```
ds-canvas init ds/canvas.md      # scaffold the canvas (REPLACE placeholders)
ds-canvas validate ds/canvas.md  # exit 0 = contract holds; exit 1 = findings
```

Python API when scripting is needed: `ds_canvas.parse(text)` → `Canvas`,
`ds_canvas.validate(canvas)` → `list[Finding]`.

## The REASONS canvas, DS meaning

| Dimension | Holds |
|---|---|
| R — Requirements | Business goal, decision the model supports, success criteria, `key_metrics` |
| E — Entities | Data definitions: datasets, sources, grain, fields (name/type/unit/role), quality rules |
| A — Approach | Task type, target, split strategy (method/column/ratios), metrics with targets, model families (baseline + candidates) |
| S — Structure | Pipeline: preprocessing ops per field (`fit_on: train` for fitted ops), artifacts, experiment tracking |
| O — Operations | Ordered implementation steps, each with an exit condition |
| N — Norms | Seed, environment lock, experiment tracking conventions |
| S — Safeguards | `target_excluded_from_features`, `test_set_single_use`, `split_before_fit` (all must be true), `pii_fields` |
| Results (optional) | Achieved metric values on test; must include the primary metric and meet its target |

Validation enforces cross-dimension checks — preprocessing fields must be
declared in E, the target must be listed in a `drop` op and appear in no
other preprocessing op, the primary metric must be an R key metric, Results
must meet declared targets.

### Vocabulary the validator accepts

- Field `type`: `string`, `integer`, `float`, `boolean`, `datetime`.
- Field `role` (optional): `key`, `feature`, `target`. The field with
  `role: target` must be A's `target`. `unit` is optional free text.
- Quality rules and their keys (all take `fields`): `unique`;
  `non_negative`; `missing_at_most` with `max` (ratio 0–1);
  `allowed_values` with `values` (non-empty list); `range` with `min`
  and/or `max`.
- Preprocessing ops: `drop`, `passthrough`, `derive`, and the fitted ops
  `impute_mean`, `impute_median`, `impute_constant`, `one_hot_encode`,
  `target_encode`, `scale_standard`, `scale_minmax`, `winsorize`. Any other
  name is an error.
- Field groups, for wide data: declare `field_groups` on a dataset (a group
  name mapped to a list of that dataset's fields), then use the group name
  in any `fields` list (quality rules, S ops, `pii_fields`). Never write a
  range as two names: `[pixel_0_0, pixel_7_7]` means exactly those two
  fields.

  ```yaml
  field_groups:
    pixels: [pixel_0_0, pixel_0_1, pixel_0_2]
  quality_rules:
    - rule: range
      fields: [pixels]
      min: 0
      max: 16
  ```

## Procedure

### 1. Init the canvas

```
ds-canvas init ds/canvas.md
```

### 2. Analysis

Fill in `analysis.md` (template in this skill directory) from the business
request and initial data look. Answer, in order:

1. Business goal — what decision changes because of this model?
2. Data understanding — sources, access, volumes, grain.
3. Framing options — candidate task types and their trade-offs.
4. Risks — target leakage, class imbalance, temporal drift, PII, volume.
5. Open questions for stakeholders.

The initial data look happens before the split exists, so it sees rows that
will become validation and test. Keep it to schema-level facts: row count,
column names and types, null counts, value ranges, the label set. Anything
distributional (class balance, correlations, per-feature statistics)
waits for EDA on the train split.

Exit: every section of `analysis.md` is filled; open questions are listed
explicitly (empty is a red flag, not a success).

### 3. Author the canvas

Fill every REPLACE placeholder in `ds/canvas.md` from the analysis. Rules of
thumb:

- E: declare every field the pipeline will touch, with type and role.
- A: one baseline family and at least one candidate family; the primary
  metric must appear in R `key_metrics`; give every metric a target
  (`op` + `value`).
- S: fitted ops (impute/encode/scale) must set `fit_on: train`; the target
  may only appear under `op: drop`.
- A: check that the test split can resolve each target. One test row moves
  a metric by 1 / n, where n is the rows the metric is computed over (for a
  per-class metric, the smallest class's test count). If the gap between
  the target and the score you expect is under about three such steps, the
  test split cannot tell a pass from a miss: enlarge the test split, loosen
  or drop the target, or record the limitation in R before any training.
- O: every step gets an exit condition that a script or a review can
  check, and that can fail. "`ds-canvas validate` clean" is not an exit
  condition for a code step, because it passes whatever the code does.
  Name output files exactly; when a file is renamed, update O in the same
  change.

Then validate, and fix until clean:

```
ds-canvas validate ds/canvas.md   # repeat until exit 0
```

Exit: `ds-canvas validate` exits 0.

### 4. Implement the pipeline

Work through O in order, one operation per working session:

1. Satisfy the operation's exit condition before moving to the next.
2. Fit preprocessing on train only; apply to validation/test (Safeguards).
3. Set every seed from N; record every experiment run per N's tracking.
   The tracking file is append-only across selection rounds: each run
   carries its round number, and a new round never overwrites an earlier
   round's runs.
4. Model selection happens on validation, never on test.

Exit: every O exit condition holds; the selected model is the best
validation performer among tracked runs.

### 5. Evaluate on test, once

Run the selected model on the test split exactly once per selection round.
Record each evaluation as one entry, with its round number, in a test
results file next to the tracking file, and make the evaluation script
refuse to run when the current round already has an entry. In that same
single run, record enough to explain a miss later (per-class or per-segment
metrics, or a confusion matrix), because the test split is not read again.

Add a `## Results` section to the canvas:

```yaml
results:
  - metric: <primary-metric-name>
    achieved: <number>
  - metric: <guardrail-metric-name>
    achieved: <number>
```

```
ds-canvas validate ds/canvas.md
```

Exit: validation exits 0 — Results includes the primary metric and meets the
declared targets. If targets are missed, do NOT re-tune on test: remove the
Results section and run a new selection round under the model-enhancements
skill, which supplies the round discipline: one written hypothesis,
validation-only selection, one test evaluation, and a stop rule. Every
extra round is another look at the same test rows, so declare before the
round whether it is the last. If the fix belongs in E or S and not in the
model layer, change the canvas first (step 7) and still follow that round
discipline.

### 6. Report

Fill in `report.md` (template in this skill directory) from the canvas:
business goal (R), data (E), approach and metrics (A), results (Results),
caveats and next steps. Every claim in the report must trace to a canvas
section.

Exit: report exists, cites the canvas, and states each metric's achieved
value and target.

### 7. Keep in sync (all later changes)

- Requirements change → update the canvas (R/E/A/S/O as needed) →
  `ds-canvas validate` → update code.
- Logic corrections found in code → fix the canvas first, then regenerate
  the affected code.
- Pure refactoring → refactor code, then update the canvas to match
  (`ds-canvas validate` after).
- Any canvas edit ends with `ds-canvas validate` exiting 0.

When code has already drifted from the canvas (landed fixes, refactors, new
pipeline code), use the ds-canvas-sync skill for the full reverse-sync
procedure: divergence inventory, triage precedence, and Results-staleness
decisions.

## Non-negotiables

- The test split is evaluated once per model selection round.
- Preprocessing that fits statistics (imputation, encoding, scaling) is fit
  on train only.
- The target never appears in features or in non-drop preprocessing.
- A canvas that does not validate is not a contract; it is a draft.
