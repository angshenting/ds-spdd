# mnist-digits

End-to-end run of the **spec-driven-ds** skill on scikit-learn's handwritten
digits. It was run as a test of the skills: an agent working only from
`skills/` and the `ds-canvas` CLI. What the skills got right and wrong is in
[`FINDINGS.md`](FINDINGS.md).

The data is `sklearn.datasets.load_digits`: 1,797 images at 8x8 pixels from
the UCI Optical Recognition of Handwritten Digits dataset. It is MNIST-like
but not MNIST. It ships with scikit-learn, so nothing is downloaded.

The demo pipeline code is example/documentation code: its verification is
the skills' exit conditions (canvas validates, quality rules pass, runs
tracked, test used once per round), not a pytest suite. The canvas validator
itself is fully tested in the repo root (`frameworks/ds-canvas/`).

## Artifacts

| Path | What it is | Produced by |
|---|---|---|
| `ds/analysis.md` | Analysis: framing, risks, open questions | spec-driven-ds step 2 |
| `ds/canvas.md` | The design contract (REASONS; no Results, because targets weren't met) | `ds-canvas init` + authoring, validated with `ds-canvas validate` |
| `data/fetch.py` | Writes `load_digits` to `data/raw/digits.csv` | O step 1 |
| `pipeline/preprocess.py` | Stratified split per A, E quality rules and EDA on train only | O step 2 |
| `pipeline/train.py` | Baseline + candidates fitted on train, selected on validation, runs tracked per round | O steps 3–4 |
| `pipeline/evaluate.py` | Test evaluation, refused if the round has already used test | O step 5 |
| `pipeline/common.py` | Paths and contract constants shared by the scripts | — |
| `reports/eda.md` | Train-only EDA and quality-rule results | O step 2 |
| `experiments/runs.jsonl` | Every validation run, both rounds | O step 4 |
| `experiments/test_results.jsonl` | One test evaluation per round | O step 5 |
| `report.md` | Stakeholder report and round record, claims traced to the canvas | spec-driven-ds step 6 |
| `FINDINGS.md` | What the run revealed about the skills and the validator | this test |

## The story

1. **Analysis.** The analysis framed the task as 10-class classification for
   a form-keying decision. It flagged that `image_id` follows label order (a
   leakage candidate, so it's dropped) and that writer IDs are missing, so
   a random split mixes writers across splits. It also predicted that about
   27 test images per digit makes a per-class floor coarse.
2. **Canvas.** Authored from the analysis. `ds-canvas validate` rejected the
   first draft with 69 errors: `int` instead of `integer` on 66 fields,
   plus three quality rules it doesn't have. The second pass was clean.
   Targets were fixed before any training: accuracy ≥ 0.97, worst digit's
   recall ≥ 0.90.
3. **Round 1** (standard scaling fitted on train). On validation:
   logistic baseline 0.9556, SVM-RBF 0.9815, kNN 0.9741. SVM-RBF was
   selected. Test, once: accuracy 0.9704 (met), worst digit 0.8846, i.e.
   23 of 26 (missed). The validator refused the Results.
4. **Round 2.** A train-only diagnostic showed scaling inflated rare edge
   pixels to z = 35. The hypothesis, verdict rule and "last round" stop were
   written in `report.md` before anything changed. The canvas S dropped
   `scale_standard` first, then the code. On validation: SVM-RBF 0.9926
   and kNN 0.9815, so the hypothesis was confirmed. But the scaling had been
   protecting kNN and the baseline's worst digit, and both now fail the
   guardrail. Test, once: accuracy 0.9852 (met), worst digit 0.8846 again
   (missed by the same single image).
5. **Stop.** Round 2 was declared last, so there is no round 3 and no Results
   in the canvas. The report hands the stakeholder a decision on R: change
   the per-class floor, measure it on more data, or add a reject option.

## Reproduce

```
uv sync
uv run python data/fetch.py
uv run python pipeline/preprocess.py
uv run python pipeline/train.py
uv run python pipeline/evaluate.py
uv run ds-canvas validate ds/canvas.md
```

Everything is seeded with 42. On the locked environment (`uv.lock`),
re-running reproduced the committed files byte for byte, with one exception. `evaluate.py` refuses to run while
`experiments/test_results.jsonl` already holds a line for the current round:
that is the single-use test safeguard working. To reproduce the test
evaluation, remove that round's line first. `train.py` reproduces round 2
only. Round 1's configuration lives on in `runs.jsonl` and `report.md`, not
in the code.
