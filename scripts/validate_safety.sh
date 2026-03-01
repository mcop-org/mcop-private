#!/usr/bin/env bash
set -euo pipefail

echo "== Safety gate =="

# 1) Block changes to RISK CORE (git diff vs main)
if git rev-parse --verify main >/dev/null 2>&1; then
  base_ref="main"
else
  base_ref="HEAD~1"
fi

changed_files="$(git diff --name-only "$base_ref"...HEAD || true)"

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

# 2) Block new deps (simple heuristic)
if echo "$changed_files" | grep -E '(^pyproject\.toml$|^requirements\.txt$|^requirements/|^Pipfile|^poetry\.lock$)' >/dev/null 2>&1; then
  echo "❌ Safety gate failed: dependency file changed (requires explicit approval)."
  echo "$changed_files" | grep -E '(^pyproject\.toml$|^requirements\.txt$|^requirements/|^Pipfile|^poetry\.lock$)' || true
  exit 1
fi

# 3) Run tests
echo "== Running tests =="
pytest -q

echo "✅ Safety gate passed."
