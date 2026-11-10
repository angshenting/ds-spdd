---
name: model-enhancements
description: Iterate at the model layer under an explicit budget — new
  candidate families, bounded hyperparameter search, class-imbalance
  handling, calibration, ensembling — with every trial on validation and
  the test split used once per round. Use when targets are unmet on clean
  data (e.g. after data-cleaning or feature-engineering closed their
  levers), when a family underperforms its declared role, or when a
  model-level change is wanted. Requires an existing valid canvas
  (`ds-canvas validate` exit 0).
---

# model-enhancements

An enhancement is a hypothesis plus a declared candidate plus a budget.
The canvas records the decision space (families, search space, budget,
calibration); the tracking file records the search; Results records the
round outcome. Anything not declared in the canvas before the search runs
is out of contract.

## Canvas surfaces

- **A (approach)** — model families gain optional blocks, both
  machine-checkable:
  - `search` on a family: `method` in {grid, random}, `budget` (positive
    integer — the declared trial cap, written before tuning), `space`
    (mapping of parameter to non-empty list). For `method: grid` the
    budget must cover the full declared space — grid is exhaustive, and a
    truncated grid is a silent lie.
  - `calibration`: `method` in {sigmoid, isotonic}, `fit_on: train`.
    Calibration changes what the metric threshold means, so it is
    contract, not a code detail.
- **N (norms)** — tracking discipline: every trial (family, params, seed,
  validation metrics) is appended to the tracking file; trials beyond the
  declared budget do not exist.
- **Results** — new round outcome; only added if declared targets are met
  (the validator rejects achieved values below target — that is correct).

A round's hypothesis may point outside the model layer, for example at a
preprocessing op in S or a field in E. That change is still a round: edit
E or S in the canvas first, validate, regenerate the affected code, and
then follow the selection law, the test-once rule and the stop rule below
unchanged. The `search` and `calibration` blocks are simply not used.

## Selection law (per round)

- Trials run on the **validation split only**. Early stopping and any
  data-driven choice inside training use train only.
- **Guardrails filter, the primary metric orders**: a trial that violates
  a guardrail on validation is not eligible, no matter how good its
  primary metric.
- The test split is evaluated **exactly once per selection round**, on the
  selected configuration.
- The metric threshold is contract. Changing it is an A change — a new,
  stakeholder-visible round — never a silent tuning knob.

## Procedure

1. **Write the hypothesis first**: what is wrong with the current round's
   model (underfit, imbalance, miscalibrated probabilities, missing family
   type), what change should fix it, and the expected effect on the
   primary metric. One hypothesis per round. Also write whether this is
   the last round: each round re-reads the same test rows, so the number
   of rounds is declared, not discovered.
2. **Declare the decision space in the canvas before running anything**:
   the candidate family (or a new family with role: candidate), its
   `search` block (method, budget, space), calibration if the hypothesis
   calls for it. Update N if trial tracking needs new fields.
3. **Validate the contract**:
   ```
   ds-canvas validate <canvas.md>
   ```
   Exit condition: exit 0.
4. **Run the search within the budget**: every trial is fitted on train,
   scored on validation, and appended to the tracking file (N) with its
   params. No trial outside the declared space; no peeking at test.
5. **Select**: guardrails filter on validation, primary metric orders.
   The winner's family and params are recorded (models/ + tracking file).
6. **Honor staleness**: A (and/or N) changed, so any existing Results are
   invalid — remove the Results section entirely, evaluate the selected
   configuration on test **once**, then:
   - targets met → re-add Results from the test run, validate (exit 0);
   - targets not met → Results stay out (see the stop rule).
7. **Report**: baseline-vs-enhanced deltas on validation and test, the
   trial count vs declared budget, and the hypothesis verdict — every
   claim traced to the canvas and the tracking file. Report the operating
   point honestly: if the winner sits at the guardrail's edge (e.g.
   precision near the base rate because the guardrail is loose), say so
   and flag the guardrail as the binding constraint for the stakeholder —
   a contract met mechanically is not the same as a model worth shipping.

## Stop rule

Iterate while both hold: (a) a concrete hypothesis remains, and (b) a
fresh declared budget justifies its cost. When either fails — targets
unmet, ideas exhausted, budget spent — stop and report the gap honestly.
The remaining options are a requirement-level conversation (renegotiate
the target in R with the stakeholder) or accepting the model's limits.
Never: lower targets silently, re-tune on test, run undeclared trials, or
extend the budget retroactively to squeeze out a pass.

## Exit conditions

- [ ] Hypothesis written before the search; decision space declared and
      validated before any trial ran
- [ ] Every trial within the declared space and budget, tracked in the
      tracking file
- [ ] Selection respected guardrails-filter-primary-orders on validation
- [ ] Test evaluated once for the round; Results added only if targets met
- [ ] Report updated with deltas, budget usage, and hypothesis verdict
