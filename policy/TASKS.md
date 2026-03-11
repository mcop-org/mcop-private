# MCOP Agent Task Templates (Source of Truth)

Goal: make it easy to delegate work safely without writing new specs every time.

Principles:
- Governance stays strict (PR + CI + CODEOWNERS).
- Tasking stays lightweight (copy/paste templates).
- Default to "Small change" unless it’s a new feature.

---

## Template A — Small Change (default)

**Task title:** <short, action phrase>

**Context:** (1–3 bullets)
- What’s happening now?
- Why do we need this change?

**Change request:**
- Do: <exact change>
- Do: <exact change>
- Do NOT: <explicit non-goals / forbidden areas>

**Files allowed to edit (tight scope):**
- <path>
- <path>

**Tests:**
- If logic changes: add/adjust pytest.
- If purely copy/UI text: tests optional but preferred.

**Acceptance criteria (must be true):**
- `pytest -q` passes
- `./scripts/validate_safety.sh` passes
- Output/diff matches requested change

---

## Template B — New Feature (mini-spec)

**Feature name:** <name>

**Purpose (1 sentence):**
- <what outcome, for whom>

**Inputs:**
- <explicit inputs + where they come from>

**Outputs:**
- <explicit outputs + where they appear>

**Determinism + safety constraints:**
- No network/API
- No randomness
- No system clock use (unless passed in as input)
- No new dependencies
- Must not modify risk core logic unless explicitly allowed

**Integration points (exact files/functions):**
- <path> : <function/class>

**Tests (minimum):**
- Determinism test
- One correctness test
- One integration/snapshot-style test if applicable

**Non-goals:**
- <what we are NOT doing>

---

## Quick “Forbidden Changes” reminder
Unless a task explicitly says so, agents MUST NOT modify:
- exposure logic
- stress logic
- commitment decision logic
- capital thresholds
- safety gate scripts