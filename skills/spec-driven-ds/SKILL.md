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
declared in E, the target must not appear in non-drop preprocessing, the
primary metric must be an R key metric, Results must meet declared targets.

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
- O: every step gets an exit condition that a script or a review can check.

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
4. Model selection happens on validation, never on test.

Exit: every O exit condition holds; the selected model is the best
validation performer among tracked runs.

### 5. Evaluate on test, once

Run the selected model on the test split exactly once. Add a `## Results`
section to the canvas:

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
Results section, go back to step 4 with validation-only tuning, and only
then re-evaluate.

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
