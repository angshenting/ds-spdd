# Model Report — churn-demo

Every claim below traces to a section of `ds/canvas.md`.

## Business goal

From R: predict which subscription customers will cancel within 30 days so
the retention team can target monthly intervention offers. Success criteria:
model meets the declared metric targets on the test split, once, with every
claim traceable to the canvas.

## Data

From E: `subscriptions`, one row per customer per month, 30,000 rows
(3,000 customers x 10 months), from `data/generate.py` (seeded; the raw
extract carries known upstream defects, fixed by the S cleaning ops — see
the cleaning record below). Fields used as features: monthly_charges (5%
missing, median-imputed from train), plan_type (one-hot, categories from
train), tenure_months, support_tickets. All four E quality rules PASS on
the train split only (`reports/eda.md`); the gate exits non-zero on any
failure.

## Approach

From A: binary classification at customer-month grain; temporal split on
month (70/15/15 by rows ordered by month); recall_at_30 primary (threshold
0.4, target >= 0.60), precision_at_30 guardrail (threshold 0.4, target
>= 0.20); families: logistic regression (baseline) and gradient boosting
(candidate). Selection on validation only.

## Results

From the model-enhancements round (2026-11-06): the candidate's declared
grid search (class-imbalance handling via positive-class weighting, budget
4, trials on validation only) selected `gradient_boosting` with
`pos_weight: 8` — validation recall 0.9765 at precision 0.3329, beating the
fixed configurations (baseline logistic 0.5521, unweighted GBM 0.5887) and
respecting the precision guardrail. On the test split, used once for this
round: **recall_at_30 = 0.9638 (target >= 0.60, met)** and
**precision_at_30 = 0.3339 (target >= 0.20, met)**. The canvas Results
section records this round; earlier rounds' numbers are history in
`experiments/runs.jsonl`.

**Read the operating point before celebrating.** At `pos_weight: 8` the
model flags the overwhelming majority of customers (precision 0.334 is
close to the 0.32 base rate), so the recall target is met mechanically.
The binding constraint is the precision floor: 0.20 is loose enough that
"flag nearly everyone" wins. Whether this operating point is useful is the
offer-budget question from `ds/analysis.md` — at precision 0.33 the
retention team wastes roughly two offers per useful one.

**Correction of record.** An earlier version of this report cited
validation numbers (GBM 0.6092, logistic 0.5535) as the cleaning round's;
those were pre-cleaning-round measurements on different (pre-dirt) data.
The corrected featureless-cleaned numbers are GBM 0.5887 / logistic 0.5521
(reproduced exactly by this round's `pos_weight: 1` and baseline trials).
The cleaning round's test measurement (0.5703, targets missed) was always
correct.

## Cleaning record

Per `ds/canvas.md` (E quality_rules + S cleaning): the raw extract carried
120 duplicate (customer_id, month) rows and 50 negative charges. Decisions:
duplicates removed pre-split (`deduplicate`), negatives clipped at 0
(`clip`) — both stateless and before the split, so split ratios held. All
four E quality rules PASS on train (`reports/eda.md`), and the gate now
exits non-zero on any failure. The round's test measurement was recall
0.5703 (target unmet) — the duplicates had been flattering earlier
measurements (0.6021 on dirty splits).

## Feature hypotheses

Two hypotheses were tested; both were rejected, and neither feature is in
the canvas:

1. `churn_history_3m` (customer's own prior churn outcomes) — **rejected by
   the validator before any code was written**: its `derived_from` provenance
   reaches the target, which the canvas defines as target leakage. Dead on
   arrival, by design.
2. `tickets_3m_mean` (mean support tickets over the prior 3 months per
   customer; causal lookback window, empty windows filled with 0) —
   **rejected as a noise-level tie in selection on validation**: 0.5894
   with the feature vs 0.5887 without — a +0.0007 difference on a feature
   that cannot carry signal in this data (support tickets are
   independent draws). The feature was removed from E and S and from the
   code; the canvas rolled back and re-validated. (An earlier version of
   this section compared against 0.6092, a pre-cleaning measurement on
   different data; comparisons across rounds are invalid — corrected here.)

The test split was not used in that round — survival was decided entirely
on validation, and losing features leave no trace in the contract.

## Caveats and next steps

Data is synthetic; absolute metric values are not indicative of real churn
performance. **Decision point for stakeholders:** the declared targets are
met, but at an operating point that flags nearly everyone — revisit the
precision floor (guardrail in A, currently >= 0.20) with the retention team
in light of offer economics, which turns "model work" into a requirement
conversation in R/A. Any new guardrail or threshold change is a new,
stakeholder-visible canvas round with its own selection cycle.
