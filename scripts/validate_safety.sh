#!/usr/bin/env bash
set -euo pipefail

echo "== Safety gate =="

head_ref="${HEAD_REF:-HEAD}"
base_ref="${BASE_REF:-}"
diff_label=""

if [[ -n "$base_ref" && "$base_ref" != "0000000000000000000000000000000000000000" ]] && git rev-parse --verify "${base_ref}^{commit}" >/dev/null 2>&1; then
  diff_label="${base_ref}...${head_ref}"
elif git rev-parse --verify main >/dev/null 2>&1; then
  base_ref="main"
  diff_label="${base_ref}...${head_ref}"
elif git rev-parse --verify origin/main >/dev/null 2>&1; then
  base_ref="origin/main"
  diff_label="${base_ref}...${head_ref}"
elif git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
  base_ref="HEAD~1"
  diff_label="${base_ref}...${head_ref}"
else
  base_ref="HEAD"
  diff_label="${base_ref}"
fi

echo "Diff base: ${base_ref}"
echo "Diff head: ${head_ref}"

if [[ "$diff_label" == "HEAD" ]]; then
  changed_files="$(git diff-tree --no-commit-id --name-only -r HEAD || true)"
else
  changed_files="$(git diff --name-only "${diff_label}" || true)"
fi

echo "Changed files evaluated:"
if [[ -n "${changed_files}" ]]; then
  printf '%s\n' "$changed_files"
else
  echo "(none)"
fi

# 2) Block changes to RISK CORE
risk_core_regex="$(awk '
  NF==0 {next}
  $0 ~ /^#/ {next}
  {gsub(/\//, "\\/"); print "^" $0}
' policy/RISK_CORE_PATHS.txt | paste -sd'|' -)"

if [[ -n "${risk_core_regex}" ]]; then
  if echo "$changed_files" | grep -E "$risk_core_regex" >/dev/null 2>&1; then
    echo "❌ Safety gate failed: protected RISK CORE paths changed."
    echo "Protected paths touched:"
    echo "$changed_files" | grep -E "$risk_core_regex" || true
    echo "Next step: stop this normal workflow."
    echo "Split the change to keep risk-core edits out of this branch, or get explicit approval before continuing."
    exit 1
  fi
fi

# 3) Block new deps (simple heuristic)
if echo "$changed_files" | grep -E '(^pyproject\.toml$|^requirements\.txt$|^requirements/|^Pipfile|^poetry\.lock$)' >/dev/null 2>&1; then
  echo "❌ Safety gate failed: dependency files changed."
  echo "Dependency files touched:"
  echo "$changed_files" | grep -E '(^pyproject\.toml$|^requirements\.txt$|^requirements/|^Pipfile|^poetry\.lock$)' || true
  echo "Next step: stop and confirm this change is intentional."
  echo "If dependency changes are not required, remove them from the branch. If they are required, get explicit approval before proceeding."
  exit 1
fi

echo "✅ Safety gate passed."
