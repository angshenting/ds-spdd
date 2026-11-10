# Findings — testing the skills on handwritten digits

What happened when an agent with only the skills (`skills/`) and the
`ds-canvas` CLI ran spec-driven-ds end to end on scikit-learn's digits. Each
finding names the step where it surfaced, what happened, and a suggested
fix. The framework source was not opened; where the CLI messages fell short,
the rule keys were looked up in `tests/`.

## Worked as intended

- `ds-canvas init` gave a usable scaffold, and the second validation pass
  was clean.
- Enum errors list the allowed values (`task`, `split.method`, field `type`,
  quality-rule names), so most mistakes fixed themselves in one pass.
- Cross-dimension checks caught everything they claim to: split ratios that
  don't sum to 1, a fitted op without `fit_on: train`, a quality rule on an
  undeclared field, and the target inside `scale_standard`.
- The Results check did its job in round 1. It refused a guardrail that
  missed by one image (`achieved 0.8846 does not meet target '>= 0.9' for
  'min_class_recall'`), so the contract couldn't claim success.

## Canvas authoring (spec-driven-ds step 3)

1. **The type vocabulary isn't documented.** `type: int` is rejected; the
   validator wants `integer`. The message lists the allowed types, but
   neither SKILL.md nor the template does (the template shows only `string`
   and `float`). One wrong word produced 66 identical errors, one per field.
   *Fix:* list the types in SKILL.md, and group repeated findings in the CLI
   output.
2. **Quality-rule keys aren't discoverable.** The CLI names the four known
   rules (`allowed_values`, `missing_at_most`, `non_negative`, `unique`) but
   not their keys (`values`, `max`). I had to find those in `tests/`. There
   is no range or upper-bound rule: 0–16 pixel bounds had to be written as a
   17-item `allowed_values` list. *Fix:* document each rule's keys in
   SKILL.md; consider a `range` rule.
3. **No way to declare a field family.** The 64 pixel names appear three
   times (E fields, a quality rule, an S op), which makes up most of the
   canvas. While writing it I used `[pixel_0_0, pixel_7_7]` as a range. YAML
   reads that as two fields, and it validated because both names are
   declared. Wide and image data makes this the main way the canvas goes
   wrong. *Fix:* a field-group or pattern declaration in E, usable wherever
   a `fields` list is.
4. **`role` is described but neither scaffolded nor checked.** SKILL.md says
   fields carry name/type/unit/role. The template omits role and unit, and
   the validator ignores role entirely (`role: banana` passes) and never
   checks that the field marked `role: target` is A's `target`.

## Validator coverage (probed with deliberate mistakes on a scratch copy)

5. **Unknown preprocessing ops only warn.** `op: scale_banana` gets a
   warning and exit 0. (This finding first said "accepted silently"; that
   was wrong, because the probe counted errors only.) The `fit_on: train`
   check only covers ops it recognises, so a misspelled fitted op (e.g.
   `scale_standrd`) escapes the train-only safeguard with a passing exit
   code. *Fix:* reject ops outside the known set.
6. **`target_excluded_from_features` is a declaration only.** Removing the
   target from the `drop` op still validates. The validator catches the
   target inside a non-drop op, but not a target that is never dropped.
7. A guardrail metric doesn't have to appear in R `key_metrics` (only the
   primary does). This is minor; it may be intended.

## Procedure and templates

8. **Initial data look against "EDA on train only".** Step 2 asks for an
   initial data look before the canvas exists; template O step 1 says EDA
   runs on the train split only. Nothing says which pre-split statistics are
   allowed. My analysis profile saw class counts and constant pixels over
   all rows, test included. *Fix:* say that the pre-split look is limited to
   schema-level facts (row count, columns, types, nulls, ranges, label set).
9. **One template exit condition can't fail.** Template O step 2,
   "Preprocessing per S — exit: `ds-canvas validate` clean", passes whatever
   the code does. I rewrote it to a check on the code itself.
10. **Nothing checks that the test split can resolve a target.** Step 3 says
    "give every metric a target" but never asks whether the test split can
    measure it. With about 27 test images per digit, one error moves
    per-class recall by 3.7 points, so the 0.90 floor allows two errors per
    class and fails on the third. `ds/analysis.md` predicted this, and round
    1 missed by exactly one image. *Fix:* add a granularity check to step 3
    (target margin compared with 1 / smallest per-class test support).
11. **Tracking semantics are only in model-enhancements.** spec-driven-ds
    step 4 says "record every experiment run per N's tracking" but not that
    the log is append-only across rounds. My first `train.py` overwrote
    `runs.jsonl`, which would have erased round 1 at round 2.
    model-enhancements says "appended". The test-once guard has the same
    gap: nothing says how to make it round-aware.
12. **The step 5 miss path doesn't name its hand-off.** spec-driven-ds says
    "go back to step 4 with validation-only tuning", but doesn't point to
    model-enhancements, which is where the round discipline, budget and stop
    rule live. Without that rule, step 5's miss → step 4 → re-test loop has
    no limit, and each extra round puts selection pressure on the test
    split.
13. **No skill owns the seam between model-enhancements and preprocessing.**
    Round 1's train-only diagnostic pointed at S (standard scaling inflates
    rare edge pixels to z = 35), not at the model layer. model-enhancements
    only covers A, N and Results. spec-driven-ds step 7 covers canvas-first
    S changes but has no round, test-once or stop-rule language. I combined
    the two by hand: step 7 for the change, model-enhancements for the
    discipline.
14. **The single test evaluation should record enough to explain a miss.**
    Both rounds missed the per-class guardrail, but `evaluate.py` recorded
    only the two declared metrics. Finding out which digit failed would mean
    reading test again after its one use. Neither skill says what to capture
    at evaluation time. *Fix:* spec-driven-ds step 5 should record per-class
    metrics, or a confusion matrix, alongside Results.
15. **A confirmed hypothesis didn't move the guardrail.** Round 2's
    hypothesis was confirmed on validation (`svm_rbf` 0.9815 → 0.9926), and
    test accuracy rose from 0.9704 to 0.9852. Yet the guardrail result on
    test was identical: 23 of 26 on the worst digit in both rounds. That is
    finding 10 in practice. The stop rule worked as written (round 2 was
    declared last before it ran), and the remaining gap is an R conversation.
16. **The canvas drifted from the code, and nothing caught it.** Making
    tracking round-aware replaced `experiments/test_result.json` with
    `test_results.jsonl`. O step 5's exit condition still named the old
    file, and the canvas kept validating, because O exit conditions are
    prose. The agent doing the work, me, didn't notice either; a final
    review did. This is the case ds-canvas-sync exists for, hit
    unintentionally in a run that changed the canvas before the code every
    other time. *Fix:* let O exit conditions declare the artifact paths they
    depend on, so the validator (or a sync check) can confirm they exist.

## Status after the fixes

The findings above describe the skills and validator as they were during
the run. This table says what changed afterwards. The canvas in this folder
was then updated to use the new features (`role: key`, a `pixels` field
group, the `range` rule); the contract it states is the same.

| # | Status | Change |
|---|---|---|
| 1 | Fixed | SKILL.md and the scaffold list the field types; the CLI collapses more than three findings of the same shape into one line plus their paths |
| 2 | Fixed | Rule keys documented in SKILL.md and the scaffold; new `range` rule (`min` and/or `max`) |
| 3 | Fixed | `field_groups` on a dataset; a group name can be used in any `fields` list. Field names are still declared one by one in E |
| 4 | Fixed | `role` must be `key`, `feature` or `target`; a `role: target` field must be A's target; the scaffold shows role |
| 5 | Fixed | An unknown preprocessing op is now an error |
| 6 | Fixed | The target must be listed in a `drop` op |
| 7 | Left as is | Guardrail metrics outside R `key_metrics` look intended |
| 8 | Fixed | Step 2 limits the pre-split look to schema-level facts |
| 9 | Fixed | The scaffold's O step 2 asks for a check on the code; step 3 says an exit condition must be able to fail |
| 10 | Fixed | Step 3 adds a test-resolution check for every target |
| 11 | Fixed | Step 4 makes tracking append-only by round; step 5 makes the test-once guard per round |
| 12 | Fixed | The step 5 miss path hands off to model-enhancements and asks for a declared last round |
| 13 | Fixed | model-enhancements covers a round whose change is in E or S |
| 14 | Fixed in the skill | Step 5 records per-class metrics at evaluation time. This example's `evaluate.py` was not re-run, because both rounds have used the test split |
| 15 | Nothing to fix | An observation about this dataset |
| 16 | Open | Step 3 now says to update O when a file is renamed, but O exit conditions are still prose the validator can't check. A machine-readable O format is a design decision |

## Outcome of the run

- spec-driven-ds steps 1–6 completed: canvas validated, pipeline built per
  O, test evaluated once per round, report written. Targets were **not**
  met: the guardrail missed by one test image in both rounds, so the canvas
  has no Results section.
- Hand-offs: model-enhancements' round discipline was used for round 2. Its
  canvas surfaces (`search`, `calibration`) weren't, because the defect was
  in S, not the model layer. data-cleaning wasn't triggered: every quality
  rule passed on clean benchmark data. feature-engineering wasn't triggered:
  no derived feature was proposed. ds-canvas-sync wasn't invoked, but it
  should have been: a tracking refactor drifted O step 5 from the code
  (finding 16). The fix was a one-line canvas edit plus re-validation, done
  without the skill's full inventory.
