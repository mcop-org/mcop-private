WEEK 3 OBJECTIVE: LEVERAGE, NOT PLUMBING.

Implement three deliverables safely:

1) Executive Metric: Cash Risk Score (0–100)
2) Behavioural Engine: Deterministic Action Recommendations
3) Report Clarity Improvements

Do not alter any existing financial calculations.

========================================
DELIVERABLE 1: CASH RISK SCORE
========================================

Create: mcop/engine/score.py

Function:
compute_cash_risk_score(payload: dict) -> dict

Output:
{
  "cash_risk_score": int,
  "score_band": str,
  "score_breakdown": dict
}

Weights:
- runway: 0.35
- pinch: 0.25
- exposure: 0.20
- stress: 0.15
- trading_health: 0.05

Bands:
0–33 GREEN
34–66 AMBER
67–100 RED

Follow exact scoring spec previously defined.
Clamp all component scores.
Final score must be int.
Include top_drivers (top 3 contributions).

No magic numbers outside declared constants.

========================================
DELIVERABLE 2: BEHAVIOURAL ENGINE
========================================

Create:
- mcop/engine/actions.py
- mcop/engine/rules.py
- policy/rules.yaml (or .json if YAML not available)

Rules:
- Deterministic
- Equality-only conditions
- AND logic only
- No eval
- No dynamic execution

Implement starter rules:
- BLOCK_IF_PINCH_14D_AND_EXPOSURE
- BLOCK_IF_SCORE_RED
- PAUSE_BUYING_IF_PINCH_14D
- TIGHTEN_SPEND_IF_PINCH_30D
- PRESALE_CAMPAIGN_WEEK_IF_AMBER_AND_PINCH_30D

Sort actions by priority desc, severity desc.
Deduplicate by action type.

No side effects.
Actions are advisory only.

========================================
DELIVERABLE 3: DECISION PACK INTEGRATION
========================================

Add to top-level JSON:
- as_of
- cash_risk_score
- score_band
- score_breakdown
- next_actions

Do not modify existing keys.
Ensure canonical JSON ordering.
Ensure deterministic output.

========================================
TEST REQUIREMENTS
========================================

Add pytest tests:

- test_score.py (bounds + monotonic checks)
- test_rules_engine.py (load + match + sorting)
- test_decision_pack_snapshot.py (golden snapshot)
- test_determinism.py (identical output twice)

All tests must pass.

========================================
COMPLETION CRITERIA
========================================

- No change to risk core logic.
- Deterministic outputs.
- Tests pass.
- No new dependencies unless approved.
- Clean separation between engine and policy.

Proceed incrementally and commit logically separated changes.