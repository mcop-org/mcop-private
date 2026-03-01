# MCOP Repo Map (for Codex and future runners)

## Always obey
- policy/CODEX_SAFETY.md
- policy/RISK_CORE_PATHS.txt
- scripts/validate_safety.sh

## Canonical commands
- Run:
  python3 -m mcop.main run --precommit-check --commit-cost-gbp 150000 --commit-due-in-days 30
- Tests:
  pytest -q
- Safety gate:
  ./scripts/validate_safety.sh

## Where outputs are written
- Decision Pack JSON:
  - writer:
  - function:
  - output dir:
  - filename pattern:
- Weekly Brief HTML:
  - writer:
  - function:
  - output dir:
  - filename pattern:

## Where key payload fields are produced
- as_of:
- pinch_14d:
- pinch_30d:
- exposure_flag:
- trading_health_score:

## Determinism rules
- JSON serialization: sort_keys=True required for Decision Pack
- List ordering: sort where order is not semantically meaningful
- Time: do not use system clock in engine logic (only passed-in date)

## Working rules for Codex (open-files mode)
- If you need to modify a file, ask the user to open it first.
- Before editing: list exact files needed.
- After editing: run ./scripts/validate_safety.sh
