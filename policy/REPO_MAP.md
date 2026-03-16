# MCOP Normal Workflow

## Always obey
- policy/CODEX_RULES.md
- policy/CODEX_SAFETY.md
- policy/RISK_CORE_PATHS.txt
- scripts/validate_safety.sh

## One-time setup
- Run `./scripts/bootstrap_repo.sh` after cloning so local git hooks are active.

## Normal task flow
1. Start from `main` and create a branch for one small task.
2. Run the Codex task on that branch with tight file scope.
3. Review the local diff before committing.
4. Run the local checks:
   - `./scripts/validate_safety.sh`
   - `pytest -q`
5. Commit with an `AI-GEN:` message.
6. Push the branch and open a PR.

## CI meaning
- `safety-gate`: checks changed files against protected paths and dependency-file rules.
- `pytest`: runs the test suite.
- Both should pass for a normal workflow-cleanup or product-safe task.

## Protected-path failures
- If `validate_safety.sh` reports protected or RISK CORE paths, stop the normal flow.
- Either remove those edits from the branch or get explicit approval for risk-core work before continuing.
- If it reports dependency-file changes, remove them unless they were explicitly approved.

## Local review commands
- Safety gate: `./scripts/validate_safety.sh`
- Tests: `pytest -q`
