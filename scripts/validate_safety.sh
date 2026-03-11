#!/usr/bin/env bash
set -euo pipefail

echo "== Safety gate =="

# 1) Compute changed files robustly for local and CI/shallow clones
if git rev-parse --verify main >/dev/null 2>&1; then
  changed_files="$(git diff --name-only main...HEAD || true)"
elif git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
  changed_files="$(git diff --name-only HEAD~1...HEAD || true)"
else
  changed_files="$(git diff-tree --no-commit-id --name-only -r HEAD || true)"
fi

# 2) Block changes to RISK CORE
risk_core_regex="$(awk '
  NF==0 {next}
  $0 ~ /^#/ {next}
  {gsub(/\//, "\\/"); print "^" $0}
' policy/RISK_CORE_PATHS.txt | paste -sd'|' -)"

if [[ -n "${risk_core_regex}" ]]; then
  if echo "$changed_files" | grep -E "$risk_core_regex" >/dev/null 2>&1; then
    echo "❌ Safety gate failed: RISK CORE paths modified."
    echo "$changed_files" | grep -E "$risk_core_regex" || true
    exit 1
  fi
fi

# 3) Block new deps (simple heuristic)
if echo "$changed_files" | grep -E '(^pyproject\.toml$|^requirements\.txt$|^requirements/|^Pipfile|^poetry\.lock$)' >/dev/null 2>&1; then
  echo "❌ Safety gate failed: dependency file changed (requires explicit approval)."
  echo "$changed_files" | grep -E '(^pyproject\.toml$|^requirements\.txt$|^requirements/|^Pipfile|^poetry\.lock$)' || true
  exit 1
fi

# 4) Run tests
echo "== Running tests =="
pytest -q

echo "✅ Safety gate passed."