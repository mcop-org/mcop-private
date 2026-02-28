# SECURITY NOTES (MCOP)

This repository contains sensitive financial data in past commits.

Rules:
- Do NOT push this repo to any remote (GitHub, GitLab, etc.) in its current history.
- If you need a remote later, create a clean repo that tracks code only:
  - keep data/ out
  - keep baselines sanitized
  - use a separate private storage for real data

If you ever must publish code:
- use git filter-repo (or BFG) to remove data from history first.
