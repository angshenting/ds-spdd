# churn-demo

End-to-end example of the **spec-driven-ds** and **ds-canvas-sync** skills:
a small churn-prediction project delivered as SPDD-style design contracts.

The demo pipeline code is example/documentation code: its verification is
the skills' exit conditions (canvas validates, quality rules pass, runs
tracked, targets met), not a pytest suite. The canvas validator itself is
fully tested in the repo root (`frameworks/ds-canvas/`).

## Artifacts

| Path | What it is | Produced by |
|---|---|---|
| `ds/analysis.md` | Phase-1 analysis | spec-driven-ds step 2 |
| `ds/canvas.md` | The design contract (REASONS + Results) | `ds-canvas init` + authoring, validated with `ds-canvas validate` |
| `data/generate.py` | Seeded synthetic data per E | spec-driven-ds step 3 (O step 1) |
| `pipeline/preprocess.py` | Split per A, quality rules on train, preprocessing per S (fit on train only) | spec-driven-ds step 3 (O steps 2-4) |
| `pipeline/train.py` | Baseline + candidates, selection on validation, runs tracked | spec-driven-ds step 3 (O step 5) |
| `pipeline/evaluate.py` | One-shot test evaluation | spec-driven-ds step 3 (O step 6) |
| `report.md` | Stakeholder report, claims traceable to the canvas | spec-driven-ds step 6 |
| `ds/sync-report.md` | Reverse-sync record after a code drift | ds-canvas-sync |
| `data/generate.py` (dirt) + S cleaning ops + E quality_rules | The data-cleaning exercise | data-cleaning |
| E `derived_from` + S `derive`/`aggregate` rules + hypothesis record in `report.md` | The feature-engineering exercise | feature-engineering |
| A `search` block (bounded grid) + `calibration` rule + Results round in `ds/canvas.md` | The model-enhancements exercise | model-enhancements |

## The story

1. Canvas authored from the analysis; `ds-canvas validate` exits 0.
2. Pipeline implemented per Operations. Gradient boosting selected on
   validation (recall 0.6092 vs. logistic baseline 0.5513); test evaluated
   once: recall 0.6021, precision 0.561 — targets met.
3. Results recorded in the canvas; validator confirms targets met.
4. **Drift**: a quick fix lands in code — `scale_standard(tenure_months)`
   added to preprocessing — without the canvas.
5. **ds-canvas-sync**: divergence inventory and triage (one contract change
   in S, no safeguard violations); canvas S updated and re-validated; the
   old Results invalidated per the staleness table (S changed); a new
   selection round ran and test was evaluated once for that round; Results
   re-established; `report.md` updated.
6. **data-cleaning**: the raw extract regresses (120 duplicate rows, 50
   negative charges). The quality gate fails loudly (exit 1). Findings
   become contract decisions: `deduplicate` + `clip` as stateless S
   cleaning ops (pre-split, ratios intact), E quality_rules become
   machine-checkable, canvas re-validates. One fresh selection round runs
   on the cleaned data — and honestly measures recall 0.5703, missing the
   0.60 target: the validator refuses the Results, which stay out of the
   canvas. Earlier 0.6021 was flattered by duplicated rows. The miss is
   the standing decision point, to be resolved at the model layer (or by
   renegotiating R with the stakeholder).
7. **feature-engineering**: two hypotheses. The first (`churn_history_3m`,
   prior churn outcomes as a feature) is rejected by the canvas validator
   itself — its provenance reaches the target, which the contract defines
   as leakage. The second (`tickets_3m_mean`, a causal 3-month lookback
   aggregate) validates, gets implemented, and measures 0.5894 on
   validation vs 0.5887 without — a noise-level tie on a feature that
   cannot carry signal, so it is removed from E, S, and the code, and the
   canvas rolls back to exactly what it was. Losing features leave no dead
   code; the test split was never touched. (Comparisons across rounds on
   different data are invalid — see the correction of record in
   `report.md`.)
8. **model-enhancements**: the recall target is unmet on clean data, so
   the candidate declares a bounded grid search before any trial runs —
   class-imbalance handling via `pos_weight: [1, 2, 4, 8]`, budget 4,
   enforced by the validator. All trials run on validation and are logged
   to `experiments/runs.jsonl`; guardrails filter, the primary metric
   orders, and `pos_weight: 8` wins. Test is evaluated once: recall
   0.9638 and precision 0.3339 — targets met, Results return to the
   canvas. The report reads the operating point honestly: precision
   0.334 is close to the 0.32 base rate, so the loose 0.20 guardrail is
   the binding constraint, and the next decision belongs to the
   stakeholder (offer budget), not the model.

## Reproduce

```
uv sync
uv run python data/generate.py
uv run python pipeline/preprocess.py
uv run python pipeline/train.py
uv run python pipeline/evaluate.py
uv run ds-canvas validate ds/canvas.md
```

Data artifacts (`data/raw/`, `data/processed/`, `models/`, `experiments/`)
are generated outputs of the commands above, seeded with 42.
