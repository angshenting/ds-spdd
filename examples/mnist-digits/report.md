# Model Report — mnist-digits

Every claim below traces to a section of `ds/canvas.md` (named in brackets)
or to the tracking files under `experiments/`.

**Status: targets not met.** The primary metric met its target in both
rounds. The guardrail (recall of the worst-read digit at least 0.90) missed
on test in both rounds by the same single image. Round 2 was declared the
last round before it ran, so the canvas carries no Results section. The
next decision is the stakeholder's (see Caveats and next steps).

## Business goal

[R] Read single handwritten digits from scanned form boxes so they no longer
need manual keying. This is an illustrative framing on a public benchmark;
there is no real stakeholder. A misread digit costs more than a manual
keystroke, so success needs both test accuracy of at least 0.97 and recall
of at least 0.90 on every digit.

## Data

[E] One dataset, `digits`: scikit-learn's `load_digits`, which is the test
partition of the UCI Optical Recognition of Handwritten Digits dataset (not
MNIST). It has 1,797 rows, one per image: 64 pixel ink counts from 0 to 16 on
an 8x8 grid, the `digit` label, and an `image_id` row key. All four quality
rules passed on the train split (`reports/eda.md`): `image_id` is unique,
`image_id` and `digit` have no missing values, `digit` is within 0–9, and
every pixel is within 0–16.

## Approach

[A] Ten-class classification. The split is stratified by digit, 70/15/15
with seed 42 [N]: 1,257 train, 270 validation and 270 test images. Classes
are balanced (122–128 per digit in train), so accuracy is the primary
metric. The guardrail, `min_class_recall`, stops a good average from hiding
one digit that is read badly. Model families: `logistic_regression`
(baseline), and `svm_rbf` and `knn` (candidates), all at library defaults
with no search. Selection rule, on validation only: runs that fail the
guardrail are excluded, then the highest accuracy wins.

[S] Round 1 standardised the 64 pixels, with the scaler fitted on train.
Round 2 removed that step. The pixels now enter unscaled, and `drop`
(`image_id`, `digit`) is the only preprocessing.

## Results

The test split was used once per round, two rounds in total, and both
evaluations are recorded in `experiments/test_results.jsonl`. Validation
runs are in `experiments/runs.jsonl`.

| Round | Selected | Validation accuracy | Validation worst digit | Test accuracy (target ≥ 0.97) | Test worst digit (target ≥ 0.90) |
|---|---|---|---|---|---|
| 1 | `svm_rbf` | 0.9815 | 0.9259 | 0.9704, met | 0.8846, **missed** |
| 2 | `svm_rbf` | 0.9926 | 0.9615 | 0.9852, met | 0.8846, **missed** |

`ds-canvas validate` refused round 1's Results (`achieved 0.8846 does not
meet target '>= 0.9' for 'min_class_recall'`). Round 2 missed the same
target, so its Results were not added either.

### Round 2: hypothesis and verdict

Hypothesis, written before the round: standard scaling inflated rarely-inked
edge pixels to z-scores of up to 35 on train, so they dominated the RBF and
Euclidean distances. Removing the scaling should raise validation accuracy
for `svm_rbf` (above 0.9815) and `knn` (above 0.9741).

Verdict, on validation: **confirmed.** `svm_rbf` went from 0.9815 to 0.9926
and `knn` from 0.9741 to 0.9815. It had a cost, though: without scaling, the
worst-read digit for `knn` and for the `logistic_regression` baseline fell
from 0.9259 to 0.8889, so both fail the guardrail and only `svm_rbf` is
eligible.

Against the baseline: `logistic_regression` scored 0.9556 on validation in
round 1 and 0.9481 in round 2. The selected `svm_rbf` beats it by 2.6 points
of validation accuracy in round 1 and 4.4 points in round 2. On test,
`svm_rbf` went from 0.9704 to 0.9852 between rounds. There were 6 trials in
total, 3 per round, each family at defaults. No search was declared, so no
budget applied.

## Caveats and next steps

- **The guardrail can't separate these models at this sample size.** The
  worst-read digit has 26 test images (0.8846 is 23/26), so a recall of at
  least 0.90 needs 24 of 26 correct. Both rounds got 23 of 26. Validation is just as
  coarse: one image is 3.7 points of per-class recall. Round 2 improved
  accuracy everywhere it was measured, and the test result for the
  guardrail didn't move. This is the binding constraint, and it is a
  question about R, not about the model.
- **Decision for the stakeholder** (this run can't make it):
  1. Renegotiate the per-class floor. That is an R change, and it needs a
     new round.
  2. Keep the floor but measure it on more data, for example the UCI
     training partition (per the UCI description, 3,823 images from writers
     not in this set; not bundled with scikit-learn) or real form scans.
  3. Add the reject option from `ds/analysis.md` (open question 1), so that
     low-confidence digits go to manual keying. That targets this exact
     failure.
- **The failing digit is not known.** `evaluate.py` recorded only the
  declared metrics, and the test split is not re-read after its one
  evaluation. A future round should log per-class recall at evaluation
  time.
- **Round 2's test score carries some selection pressure.** Round 2 ran
  because round 1 missed on test. Its change came from a train-only
  diagnostic and was judged on validation, but the score is still a second
  look at the same 270 images, not a fresh estimate.
- **Writer leakage** (`ds/analysis.md`): writer IDs aren't available, so the
  random split mixes each writer's handwriting across train, validation and
  test. Accuracy on new writers is likely lower than reported.
- **No further model-layer round is planned.** The stop rule declared
  before round 2 applies until R is revisited.
