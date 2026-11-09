# Analysis — <project-name>

## Business goal

What decision changes because of this model? Who makes it, and how often?

## Data understanding

Sources, access method, volumes, grain (one row per what). What the join
keys are if multiple tables.

## Framing options considered

Candidate task types (e.g. binary classification vs. regression vs. ranking),
and the trade-offs that ruled each in or out.

## Risks

- Target leakage candidates (fields that encode the outcome)
- Class imbalance / distribution concerns
- Temporal drift
- PII / privacy constraints
- Data volume vs. model family appetite

## Open questions for stakeholders

Numbered list. Each question says what gets blocked until it is answered.
