# Canvas Sync Report

One report per sync. Overwrite the previous one — history lives in version
control.

## Divergence inventory

Compare `ds/canvas.md` against what the code actually does. Every dimension
gets at least one row.

| # | Dimension | Canvas says | Code does | Verdict |
|---|---|---|---|---|
| 1 | R | Retention targeting, key metric recall_at_30 | unchanged; no requirement touched | in-sync |
| 2 | E | 7 fields incl. tenure_months (integer) | schema unchanged; tenure still read, now standardized downstream | in-sync |
| 3 | A | temporal split 70/15/15, target churned_next_30d, recall/precision at 0.4, logistic + GBM | split, target, metrics, families unchanged | in-sync |
| 4 | S (structure) | ops: impute_median(monthly_charges), one_hot_encode(plan_type), drop(target, customer_id, month) | ops as declared PLUS scale_standard(tenure_months), fit on train (mean 4.00, std 2.00 from train split) | contract-change |
| 5 | O | steps 1-8 incl. preprocess/train/evaluate | step flow unchanged; preprocess step now also scales tenure | contract-change (consequence of #4) |
| 6 | N | seed 42, uv + lock, tracking file at experiments/ | seed 42 everywhere, uv.lock present, runs appended to experiments/runs.jsonl | in-sync |
| 7 | Safeguards | target excluded from features; test single use; split before fit; pii [customer_id] | verified in code: split happens before any fit; scale params computed from train only; target only used as label; test evaluated once in this new selection round; customer_id dropped from features | in-sync |

## Decisions

- Safeguard violations found (must be fixed in code, never synced): none.
- Contract changes applied to the canvas (sections + what changed):
  - S preprocessing: add `- op: scale_standard, fields: [tenure_months],
    fit_on: train` (matches the landed code; fitted values from train only).
  - O step 4 exit condition unchanged in substance (fitted values logged) —
    no wording change needed; O step list stays as written.
- Canvas-only drift (implement in code or remove from canvas — which, and
  why): none — all drift was code-first.

## Results staleness

- Contract-relevant sections changed (E / A / S — list, or "none"): S — a
  fitted preprocessing op was added after the first test evaluation.
- Verdict: Results removed, then re-established
- Reason: S changed → per the staleness table the old Results (first
  selection round) are invalid. A new selection round ran on validation and
  the test split was evaluated once for that round; Results now records the
  new round's values.

## Post-sync validation

- `ds-canvas validate ds/canvas.md` exit code: 0
- `report.md` updated (yes/no) and why: yes — Results provenance now cites
  the post-sync selection round, and the report records the sync.
