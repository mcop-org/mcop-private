# Sales Director v1 — Specification (Deterministic, Read-Only)

## Purpose
Provide a deterministic, advisory-only Sales Director output that identifies:
1) dormant clients
2) near-term sales focus
3) concrete recommended actions (no side effects)

This is a reporting/decision-support module only. It MUST NOT modify any financial core logic.

## Safety + Governance Constraints (Non-Negotiable)
- No network calls, no APIs, no email/Slack/webhooks.
- No randomness.
- No use of system clock for business logic. Only use explicit as_of passed in.
- No new dependencies.
- Pure/read-only analysis: MUST NOT mutate input objects.
- Output must be deterministic for identical inputs.
- No changes to exposure logic, stress logic, commitment decision logic, or capital thresholds.

## Integration Contract

### Inputs (must be passed explicitly)
Sales Director will receive a single dict `ctx` with these keys:

Required:
- ctx["as_of"]: str  (YYYY-MM-DD)  # the same as payload/base as_of
- ctx["activity_rows"]: list[dict] # loaded from inputs.activity (already used by MCOP ingest)
- ctx["products_rows"]: list[dict] # loaded from inputs.products
Optional (if already computed elsewhere, passed through read-only):
- ctx["drift_signals"]: list[str]
- ctx["pinch_14d"]: dict
- ctx["pinch_30d"]: dict
- ctx["exposure_flag"]: str
- ctx["score_band"]: str
- ctx["cash_risk_score"]: int

### Activity row minimum fields (best-effort mapping)
The director must work even if extra fields exist, but expects these columns if present:
- client_id (or customer_id)
- client_name (or customer_name)
- order_date (ISO date or parseable date string)
- order_value_gbp (numeric)
If some are missing, the director must degrade gracefully (skip that record).

### Outputs (top-level JSON block added to Decision Pack only)
Decision Pack gets a new key:
- "sales_director": { ... }

Schema:
sales_director = {
  "as_of": "YYYY-MM-DD",
  "summary": [
     "string",
     ...
  ],
  "dormant_clients": [
     {
       "client_id": "string",
       "client_name": "string",
       "last_order_date": "YYYY-MM-DD",
       "months_since_last_order": int,
       "lifetime_value_gbp": float,
       "last_12m_value_gbp": float
     },
     ...
  ],
  "focus_list": [
     {
       "client_id": "string",
       "client_name": "string",
       "reason": "string"
     },
     ...
  ],
  "recommended_actions": [
     {
       "type": "string",
       "priority": int,
       "owner": "Sales",
       "due_in_days": int,
       "message": "string",
       "triggered_by": ["string", ...]
     },
     ...
  ]
}

Determinism rules:
- Lists must be deterministically sorted (see Sorting section).
- Numeric outputs must be rounded to 2 decimals where relevant.
- Never include “generated_at/now” timestamps.

## Definitions (v1)

### Dormant client definition
A client is "dormant" if:
- they have at least 1 historical order AND
- months_since_last_order >= 3  (exact threshold constant)

### Focus list definition
Focus list is the top 10 clients ranked by:
1) highest last_12m_value_gbp (desc)
2) then highest lifetime_value_gbp (desc)
3) then client_name (asc)

But only include clients who are dormant.

### Recommended actions (v1 rules)
Generate advisory actions from deterministic conditions:

A1: REACTIVATE_TOP_DORMANT
- Trigger: at least 5 dormant clients exist
- Action:
  - type: "REACTIVATE_TOP_DORMANT"
  - priority: 80
  - owner: "Sales"
  - due_in_days: 7
  - message: "Contact top dormant clients by 12m value (start with top 5)."

A2: WINBACK_SEQUENCE
- Trigger: any dormant client has last_12m_value_gbp >= 5000
- Action:
  - type: "WINBACK_SEQUENCE"
  - priority: 70
  - owner: "Sales"
  - due_in_days: 10
  - message: "Run a winback sequence for high-value dormant accounts (>=£5k in last 12m)."

A3: CASH_PULL_PRESELL (optional passthrough alignment)
- Trigger: ctx["score_band"] in {"AMBER","RED"} AND pinch_30d.cash_alert in {"AMBER","RED"}
- Action:
  - type: "CASH_PULL_PRESELL"
  - priority: 60
  - owner: "Sales"
  - due_in_days: 7
  - message: "Prioritise presell cash pull: focus outreach on accounts most likely to commit this week."
  - Note: this must not modify existing engine actions; it is inside sales_director only.

All actions must include triggered_by listing which rule(s) fired.

### Sorting
- dormant_clients:
  1) months_since_last_order desc
  2) last_12m_value_gbp desc
  3) client_name asc

- recommended_actions:
  1) priority desc
  2) due_in_days asc
  3) type asc

- focus_list:
  As defined above (top 10)

## Implementation Requirements
- Must be implemented in a new module: mcop/directors/sales.py
- Must expose: compute_sales_director(ctx: dict) -> dict
- Must not import pandas (use stdlib only) unless pandas is already core to the repo path being used.
- Must parse dates deterministically; invalid dates are skipped (not fatal).

## Tests (pytest)
Must include:
1) Determinism: same ctx twice => identical dict output
2) Dormant classification correctness (>=3 months)
3) Sorting correctness for dormant_clients and recommended_actions
4) Integration snapshot: Decision Pack includes sales_director with stable ordering

## Non-goals (explicit)
- No emailing clients.
- No CRM integrations.
- No probabilistic churn modeling.
- No LLM calls.
- No modifying pricing, contracts, or finance logic.