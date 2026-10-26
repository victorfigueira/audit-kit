---
name: audit-diff
description: >-
  Review branch changes against a base branch using audit-kit's Diff mode before opening a PR or merging.
  A triage agent picks which auditors to run based on modified files.
---

# Diff Code Review

Review git branch changes against a target base branch to produce a merge verdict (Ready to merge, Fix before merge, Block merge).

## Arguments
- `[base-branch]`: The target branch to compare against (e.g. `main`, `master`, `develop`). If omitted, defaults to the default branch in `audit/project-context.md` or git remote default.
- `no-update`: Skip the automatic check for a newer version of audit-kit.

## Procedure
1. Read `audit-kit/RUN.md`, focusing on the "Diff mode" section.
2. If `no-update` is present, skip the update check.
3. Run the triage agent with `audit-kit/agents/triage.md` in Diff mode against the base branch.
4. Present the triage plan table and obtain user confirmation before running selected auditors.
5. Run the selected auditors in parallel using `invoke_subagent` following `audit-kit/adapters/antigravity/subagents.md`, or sequentially if subagents are unsupported.
6. Verify Critical and High findings with the skeptic verifier (using parallel `invoke_subagent` where supported).
7. Write individual reports to `audit/diff/<dimension>.md` and the final verdict summary to `audit/diff/DIFF-AUDIT.md`.
