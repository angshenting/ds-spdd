# Analysis — churn-demo

## Business goal

Predict which subscription customers will cancel within 30 days, so the
retention team can target intervention offers at the customers most likely
to churn. The decision changes: who gets a retention offer each month. The
model is reviewed monthly against the canvas targets before the retention
team acts on it.

## Data understanding

One source table, `subscriptions`: one row per customer per month, synthetic
for this demo. Access: `data/raw/subscriptions.csv`, produced by
`data/generate.py` (seeded, reproducible). Volume: ~30,000 rows (3,000
customers x 10 months). Join key: (customer_id, month). Fields: customer_id
(key), month (YYYY-MM, temporal ordering), monthly_charges (USD, ~5%
missing), plan_type (standard/premium), tenure_months, support_tickets,
churned_next_30d (target, prospective).

## Framing options considered

- Binary classification at customer-month grain (chosen): matches the
  monthly intervention decision and the label definition.
- Survival analysis over tenure: rejected for the demo — richer output than
  the retention workflow needs.
- Rule-based score (no model): rejected — no learning-based baseline to
  compare against; business explicitly wants a trained model.

## Risks

- Target leakage candidates: any field that encodes post-churn state; none
  exist in this schema — churned_next_30d is prospective and excluded from
  features by the drop op.
- Class imbalance: expected churn rate ~25-30%, mild; recall is the primary
  metric, threshold fixed in the metric definition.
- Temporal drift: charges/plans may drift by month; handled by temporal
  split — no future month ever trains a model.
- PII: customer_id is an identifier; excluded from features, listed in
  pii_fields.
- Data volume: 30k rows is ample for logistic regression and gradient
  boosting; deep models would be underfit — not considered.

## Open questions for stakeholders

1. Offer budget: how many customers can the retention team contact per month?
   Blocks: guardrail choice (precision floor) — until answered, we use
   precision >= 0.20 as a placeholder.
2. Label horizon: 30 days assumed; if the business means 60, the target
   definition and data generation must change before training. Blocks: all
   model work.
