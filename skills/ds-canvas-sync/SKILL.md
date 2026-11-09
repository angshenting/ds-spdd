---
name: ds-canvas-sync
description: Reverse-syncs pipeline code changes back into ds/canvas.md (the
  SPDD code-to-canvas direction) in a project set up with spec-driven-ds. Use
  when pipeline code has drifted from the canvas after refactors, bug fixes, or
  new preprocessing/metrics/model code; before reporting results that cite
  facts the code changed; when ds-canvas validate fails on an existing canvas;
  or when a reviewer asks whether the canvas still describes the code.
---

# ds-canvas-sync

Sync is the **code → canvas** direction. It makes the canvas an accurate
record of the code that exists, after the code changed first (quick fix,
refactor, landed experiment). It never introduces new requirements.

What sync must never do:

- **Never edit Safeguards.** Safeguards are one-way: code must come up to
  the safeguard, the safeguard never comes down to the code. A safeguard
  "update" is a requirements change, not a sync.
- **Never edit R.** Business goal and success criteria come from
  stakeholders. If code reality conflicts with R, stop and route it through
  the spec-driven-ds procedure instead (requirements → canvas → code).
- **Never re-evaluate the test split** as part of sync. Test evaluation
  belongs to the evaluation phase, once per selection round.

## Where reality lives

| Canvas section | What to inspect in the code |
|---|---|
| E — fields | data loading / schema code, feature accessors |
| A — split, target, metrics, families | split module, evaluation module, training scripts and configs |
| S — preprocessing ops | transform code: which ops run, on which fields, fit on what |
| O — steps | pipeline entry points, stage order |
| N — seed, env, tracking | config files, lock file, tracking client setup |
| S — safeguards | facts of the run — verify them, never edit them |

## Procedure

### 1. Establish ground truth

Read or run the pipeline and write down what the code *actually* does now:
preprocessing ops, their fields, and what each is fit on; split method,
column, ratios; target; metrics computed and any thresholds used in
selection; model families trained and their roles; seed, environment
manager, tracking location; the ordered pipeline steps.

Exit: the inventory is written down — it becomes the "Code does" column
below.

### 2. Inventory the divergence

Fill the divergence table in `ds/sync-report.md` (template in this skill
directory). Every dimension gets at least one row, even if the verdict is
"in-sync". Compare canvas against the inventory, line by line, dimension by
dimension.

Exit: every dimension (R, E, A, S, O, N, safeguards) has a row with a
verdict.

### 3. Triage, in this precedence order

1. **Safeguard violation** (target in features, fitting on validation/test,
   test set reuse) → stop syncing that item. Fix the code. Re-verify. The
   canvas is not touched.
2. **Requirement change** (anything in R, or anything a stakeholder would
   call a goal/success-criterion change) → out of scope. Route through the
   spec-driven-ds procedure: update the canvas from requirements first, then
   the code.
3. **Contract change** (E/A/S/O behavior differs in code) → update the
   canvas to match the code.
4. **Refactor-only** (same behavior, different structure/naming) → update
   canvas wording (O step text, S prose), not contract values.
5. **Canvas-only drift** (canvas declares something the code never
   implemented) → decide deliberately: implement it in code (the contract
   was right) or remove it from the canvas (it was never agreed). Record
   which and why in the sync report.

Exit: every row has one of: in-sync, safeguard-violation, requirement-change,
contract-change, refactor-only, canvas-only.

### 4. Apply canvas updates

Edit one section at a time, and after each edit:

```
ds-canvas validate ds/canvas.md
```

The sync is blocked until this exits 0. A canvas that does not validate is a
draft, not a contract.

### 5. Decide Results staleness

| What changed in code | Results verdict |
|---|---|
| Nothing contract-relevant (O wording, N tooling, pure refactors) | keep Results |
| Preprocessing ops or their fields (S), data fields (E), split/target/metrics/families (A) | remove the Results section, re-run selection on validation, re-evaluate on test once (spec-driven-ds evaluation phase) |
| Results already absent | nothing to do |

Record the verdict and the reason in the sync report. Never keep Results that
were produced under a different split, preprocessing, or metric definition.

### 6. Update the report

If `report.md` cites facts that changed (metrics, preprocessing, split,
families), update those claims. Every report claim must still trace to a
canvas section.

### 7. Record and exit

Complete the decisions and post-sync sections of `ds/sync-report.md`
(overwrite the previous sync — history lives in version control). Exit
checklist:

- [ ] every dimension has a divergence row with a verdict
- [ ] no safeguard violations outstanding
- [ ] `ds-canvas validate ds/canvas.md` exits 0
- [ ] Results kept-or-removed is recorded with a reason
- [ ] `report.md` claims trace to the current canvas

## Non-negotiables

- Safeguards and R are never edited by sync.
- Validation failure blocks the sync until fixed.
- Test evaluation happens only in the evaluation phase, once per selection
  round — never as part of sync.
