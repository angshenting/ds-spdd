# Analysis — mnist-digits

The data is scikit-learn's bundled `load_digits` set. That is the test
partition of the UCI "Optical Recognition of Handwritten Digits" dataset,
not MNIST: 8x8 images rather than MNIST's 28x28. The folder name follows the
request that started this run. No stakeholder exists, so the business framing
below is illustrative. The run's purpose is to exercise the spec-driven-ds
skill end to end on a public benchmark.

## Business goal

Illustrative framing: a forms-processing team keys single handwritten digits
from scanned forms by hand. The model decides, per digit box, whether the
digit is read automatically or sent to manual keying. A misread digit that
goes through unchecked costs more than a manual keystroke, so overall
accuracy matters, and no single digit may be read badly. Weak recall on one
class would corrupt every form field that contains that digit. The decision
runs once per digit box, continuously.

## Data understanding

- Source: `sklearn.datasets.load_digits`, written to `data/raw/digits.csv`
  by `data/fetch.py`. It ships inside scikit-learn, so no network access or
  credentials are needed.
- Volume: 1,797 rows, 66 columns.
- Grain: one row per handwritten digit image.
- Fields: `image_id` (row number added by `fetch.py`); `pixel_0_0` …
  `pixel_7_7`, 64 integer ink counts from 0 to 16 (each 8x8 cell is a count
  of set pixels in a 4x4 block of the original 32x32 bitmap); `digit`, the
  label from 0 to 9.
- Single table, so there are no join keys.
- Initial look, schema level only: no nulls, every value is an integer,
  pixels span 0–16, `image_id` is unique, no two rows share an identical
  pixel vector, and classes are balanced (174–183 images per digit).
  Distribution-level EDA is O step 1, on the train split only.

## Framing options considered

- **10-class classification (chosen).** It matches the decision directly:
  read the digit. Classes are balanced, so plain accuracy is a fair primary
  metric. A per-class recall floor guards against one digit being sacrificed
  for the average.
- **Ten one-vs-rest binary problems.** Rejected. It gives ten models and ten
  thresholds to own, with no gain over a native multiclass model at this
  scale.
- **Classification with a reject option** (abstain below a confidence
  threshold and route to manual keying). This is the closest match to the
  real decision, but it needs a stakeholder-set manual-keying budget that
  doesn't exist yet (open question 1). It is deferred as a next step and not
  built speculatively.

## Risks

- **Target leakage:** `image_id` is a row number, but row order is not
  independent of the label. The file opens in a strict 0–9 cycle (the first
  30 labels are 0,1,…,9 three times). Across the whole file
  `image_id % 10 == digit` holds for only 9.6% of rows, which is chance
  level, but a model could still pick up local order. `image_id` is dropped
  from the features and used only as the row key.
- **Class imbalance:** none (174–183 per class). Per-class test support is
  small, though: about 27 images per digit in a 15% test split, so one error
  moves a class's recall by about 3.7 points. The per-class guardrail is
  noisy at this size.
- **Writer leakage:** the UCI description says the test partition came from
  13 writers who were not in the original training partition. Writer IDs are
  not included, so a random split puts the same writer's handwriting in
  train, validation and test. Test accuracy will then be optimistic for
  handwriting from new writers. This cannot be fixed with the fields
  available.
- **Temporal drift:** none observable. There is no time column, and the
  scans come from a single collection.
- **PII:** none. Images are anonymous 8x8 count grids with no writer
  identity.
- **Volume against model appetite:** 1,797 rows with 64 features is small.
  Linear models, kernel SVMs and nearest-neighbour models fit; deep models
  would be data-starved and are out of scope.

## Open questions for stakeholders

1. What manual-keying rate is affordable? This blocks the reject-option
   framing (abstain below a confidence threshold); until it is answered the
   model always predicts.
2. Will production scans come from writers not seen in training? If yes,
   the random-split test score is optimistic, and a writer-grouped split
   (which needs writer IDs from the original NIST forms) is required before
   the accuracy can be signed off for deployment.
3. Do production scans go through the same NIST preprocessing (32x32
   normalised bitmap reduced to 8x8 counts)? This blocks any claim that the
   reported accuracy transfers to the production pipeline.
