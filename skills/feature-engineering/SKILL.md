---
name: feature-engineering
description: Add derived features (interactions, transforms, group
  aggregates) to an existing DS project as validated canvas contract —
  hypothesis first, provenance declared in E, constructed by S ops, won or
  lost in selection on validation, losers removed from the contract. Use
  when the model needs features the raw data does not expose, when a
  candidate family requires transforms, or after data-cleaning leaves
  targets unmet and richer signal might close the gap. Requires an existing
  valid canvas (`ds-canvas validate` exit 0).
---

# feature-engineering

A feature is a contract line, not a code line. Every feature is: declared
in E with provenance, constructed by an S op, consumed by model families,
and justified by a hypothesis — and features that lose in selection are
removed from the contract, never left as dead code.

## Canvas surfaces

- **E (entities)** — derived fields carry `derived_from: [fields]`
  (provenance). The validator:
  - rejects `derived_from` entries not declared in E
  - rejects the target field declaring `derived_from`
  - rejects any field whose provenance closure transitively reaches the
    target (target leakage — this is the strongest guard in the tool)
  - warns on a derived field no op produces
- **S (structure)** — two feature-construction ops:
  - `derive` — row-local, stateless arithmetic: `fn` in
    {product, ratio, log1p, indicator}, `output` = the field it creates
    (must be declared in E). Legal in `cleaning` (pre-split) or
    `preprocessing` (post-split).
  - `aggregate` — group-level lookback windows: `fields` = source column,
    `group_by` = key, `lookback` = prior rows within the group (positive
    integer), `fn` in {sum, mean, min, max, count}, `output` = the field
    it creates. Legal in `cleaning` only — windows need the full ordered
    history (ordering column = A `split.column` for temporal projects), and
    they never look forward.
- **A (approach)** — unchanged unless the feature motivates a new model
  family; features are selected per family on validation, not on test.

## Leakage law

The window looks only at prior rows within the group, and the provenance
closure must never reach the target. If the validator rejects a proposed
feature as target leakage, the hypothesis is dead — record it and move on.
Do not work around it: if prior labels are genuinely required, that is a
requirement-level conversation about the target definition in E/A, not a
feature to smuggle in via `derived_from`.

## Procedure

1. **Write the hypothesis first**: which R question does this feature
   serve, what signal does it expose, and what effect do you expect on the
   primary metric? One feature per hypothesis.
2. **Declare it**: E gains the field with `derived_from` provenance; S
   gains the producing op (`derive` or `aggregate`) with exact params.
3. **Validate the contract**:
   ```
   ds-canvas validate <canvas.md>
   ```
   Exit condition: exit 0. A leakage rejection at this step means the
   hypothesis is dead — record it, remove the declaration, stop here.
4. **Implement exactly what the canvas says** — the op in code matches the
   op in S (same params, same window semantics), no more, no less.
5. **Honor staleness**: E and/or S changed, so Results (if present) are
   invalid — remove the Results section entirely and run one full
   selection round: train → select on validation → evaluate test once.
6. **Decide survival on validation** — compare the primary metric with and
   without the new feature **on this round's data** (re-run the without-
   feature configuration in the same round if needed; never compare against
   numbers logged in earlier rounds — different rounds see different data):
   - the feature improves the primary metric by more than a pre-declared
     margin → it stays in the contract (declare the margin with the
     hypothesis; ties and noise-level differences go to the house — a
     feature that cannot carry signal by construction never ships on a
     lucky validation draw);
   - otherwise → remove it from E and S (roll the canvas back), and
     record the hypothesis as tested-and-rejected in the report.
7. **Record the outcome**: if the round meets declared targets, re-add
   Results and validate (exit 0); if not, Results stay out — never lower
   targets or re-tune on test to manufacture a pass.
8. **Update the report**: hypothesis, decision, evidence, and where the
   feature now lives (contract or rejected list) — every claim traced to
   the canvas.

## Safeguards checklist (non-negotiable)

- `aggregate` windows look only at prior rows within the group — never
  the current row's future, never across the time boundary.
- Nothing is fitted on anything but the train split; `derive` and
  `aggregate` are stateless by design.
- The target never appears in any op's fields, group_by, or provenance.
- The test split is touched exactly once per selection round.
- Removing a losing feature is a canvas rollback, not just a code change.

## Exit conditions

- [ ] Every feature has a written hypothesis and a decision
- [ ] `ds-canvas validate` exits 0 at the end (features present or rolled
      back)
- [ ] No derived field remains that lost selection
- [ ] One fresh selection round run per feature set change
- [ ] Report updated with hypothesis outcomes, claims traceable
