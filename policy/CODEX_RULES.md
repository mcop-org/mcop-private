# Codex Operating Rules (MCOP)
- Do not add network calls, secrets, or credentials handling.
- Do not modify liquidity/exposure/stress/commit decision logic unless explicitly asked.
- Prefer small, surgical diffs.
- Deterministic outputs only (stable sorting; no timestamps).
- Add/extend pytest tests for new behavior.
- If unclear about data columns, inspect ingest schemas or print df.columns in a one-off snippet (do not hardcode guesses).
