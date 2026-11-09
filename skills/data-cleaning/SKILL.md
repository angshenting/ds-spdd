---
name: data-cleaning
description: Turn data-quality findings (duplicates, invalid values, type
  drift, missingness beyond tolerance, category typos) into a validated
  canvas contract and a pipeline that fails loudly when the data stops
  meeting it. Use when EDA or the E section's quality rules fail, when a
  raw extract is known to be dirty, or when preprocessing needs new
  cleaning ops. Requires an existing valid canvas (`ds-canvas validate`
  exit 0); for greenfield canvases use spec-driven-ds first.
---

# data-cleaning

Cleaning is a contract change, not a patch. Every fix is a decision
recorded in the canvas; the pipeline enforces it and fails loudly when the
data regresses.

## Canvas surfaces

- **E (entities)** — `quality_rules` under each dataset, machine-checkable
  by `ds-canvas validate`:
  - `unique` (fields are the uniqueness key)
  - `non_negative`
  - `missing_at_most` (requires `max`, a ratio between 0 and 1)
  - `allowed_values` (requires non-empty `values` list)
  Rule fields must be declared in the same dataset.
- **S (structure)** — two op blocks with a strict placement law:
  - `cleaning:` ops run **before the split**, must be stateless, and must
    not declare `fit_on`: `deduplicate` (fields = dedupe key),
    `coerce_type`, `clip` (at least one of `min`/`max`, numbers).
  - `preprocessing:` ops run per split; anything fitted (imputers,
    encoders, scalers, `winsorize`) lives here and must declare
    `fit_on: train`.
  - The validator rejects: fitted ops in `cleaning`, `fit_on` on cleaning
    ops, `deduplicate` in `preprocessing` (row removal after the split
    breaks the ratios), the target under any cleaning op, and `clip` with
    `min > max`.
- **O (operations)** — must show the order: clean → split → quality gate on
  train → preprocess (fit on train) → train/select → evaluate once.

## Procedure

1. **Inventory findings.** Read the canvas and the latest EDA report
   (`reports/eda.md`). List every quality problem with its evidence
   (rule, field, observed value/rate).
2. **Decide per finding** — one of, and only one of:
   - fix with a stateless op → S `cleaning` (pre-split)
   - fix with a fitted op → S `preprocessing` with `fit_on: train`
   - drop rows → only via `deduplicate` (pre-split, on the declared key)
   - drop the field → remove from E and every op that referenced it
   - document only → note it in E prose; no op, no rule
   A finding with no decision is a decision left to the code — not
   allowed.
3. **Record rules in E.** Add a `quality_rules` entry for every
   invariant the cleaned data must hold (e.g. `non_negative` after a
   `clip`, `unique` after `deduplicate`, `missing_at_most` before
   imputation).
4. **Update the canvas**: E (types, notes, `quality_rules`), S
   (`cleaning`/`preprocessing` ops), O (step order above). Then:
   ```
   ds-canvas validate <canvas.md>
   ```
   Exit condition: exit 0.
5. **Implement exactly what the canvas says** — no op exists in code that
   is not declared, no declared op missing from code.
6. **Fail loudly.** The pipeline step that checks quality rules must
   verify every E `quality_rule` on the train split and exit non-zero on
   the first failure, writing what failed to the EDA report.
7. **Honor staleness.** E and/or S changed, so the canvas Results are
   invalid: remove the Results section entirely (an empty Results section
   is a validation error), run one full selection round (train → select on
   validation → evaluate test once), then:
   - if the round meets the declared targets, re-add Results from the new
     test run and `ds-canvas validate` (exit 0);
   - if it does not, **Results stay out of the canvas** — the validator
     rejects achieved values below target, and that is correct. Do not
     lower targets or re-tune on test to manufacture a pass. Document the
     miss in the report and surface the decision point: iterate at the
     model layer (new candidates/hyperparameters, selected on validation)
     or renegotiate the requirement in R with the stakeholder.
8. **Update the report**: what was found, what was decided, why, and the
   new Results — every claim traced to the canvas.

## Safeguards checklist (non-negotiable)

- Nothing is fitted on anything but the train split (`split_before_fit`).
- Row removal happens only before the split; ratios in A stay intact.
- The target never appears under any cleaning op (leakage).
- PII handling in Safeguards is unchanged by cleaning.
- The test split is touched exactly once per selection round.

## Exit conditions

- [ ] Every finding has a decision recorded in the canvas
- [ ] `ds-canvas validate` exits 0
- [ ] Quality gate passes on train and fails non-zero when a rule breaks
- [ ] One fresh selection round run; Results re-added if targets met, the
      miss documented in the report if not
- [ ] Report updated, claims traceable
