# SALES DIRECTOR v1 — IMPLEMENTATION TASK (STRICT)

You are working in MCOP. Follow CODEX_SAFETY.md. Deterministic, no new deps, no network, no exec/eval, no time.now, no randomness. Do NOT modify risk core paths.

## Goal
Implement Sales Director v1 exactly to spec:
- Spec source: policy/directors/sales_director_v1.md
- Output: deterministic director report + actions.

## Create files
- mcop/directors/sales.py
- tests/test_sales_director.py

Optional (only if needed for imports):
- mcop/directors/__init__.py

## Required API
Implement:
def compute_sales_director(ctx: dict) -> dict

Must NOT mutate ctx. Must be pure and deterministic.

## Inputs (ctx)
Must accept:
- as_of: str (YYYY-MM-DD)
- activity_rows: list[dict]
- products_rows: list[dict]

May accept (pass-through):
- drift_signals, pinch_14d, pinch_30d, exposure_flag, score_band, cash_risk_score

## Dormant client rule
Dormant if:
- client has >= 1 historical order
- months_since_last_order >= 3
Define months deterministically (document the method). No datetime.now().

Missing/invalid dates: skip that record.

## Sorting (STRICT)
Dormant clients:
1) months_since_last_order DESC
2) last_12m_value_gbp DESC
3) client_name ASC

Focus list:
1) last_12m_value_gbp DESC
2) lifetime_value_gbp DESC
3) client_name ASC

Recommended actions:
1) priority DESC
2) due_in_days ASC
3) type ASC

Stable sorting required.

## Tests (pytest)
In tests/test_sales_director.py include:
- determinism test (same input twice => identical output)
- dormant threshold test (>=3 months included, <3 excluded)
- sorting test (verify ordering rules)
- empty dataset test
- high-value dormant triggers WINBACK rule (per spec)

All tests must pass:
pytest -q
./scripts/validate_safety.sh