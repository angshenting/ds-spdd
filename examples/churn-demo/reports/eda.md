# EDA (train split only)

- rows: 21000
- churn rate: 0.330
- monthly_charges missing rate: 0.050
- quality rules: unique [customer_id, month]: PASS; non_negative [monthly_charges]: PASS; missing_at_most [monthly_charges] max 0.05: PASS; allowed_values [plan_type]: PASS
