---
name: audit
description: >-
  Run a Standard code audit with the audit-kit team (incremental when a previous audit exists).
  Evaluates maintainability, open-source health, architecture, security, and reliability.
---

# Standard Code Audit

Run a Standard code audit using the audit-kit team.

## Arguments
- `fresh`: Force every auditor to run and skip triage, ignoring previous findings.
- `no-update`: Skip the automatic check for a newer version of audit-kit.

## Procedure
1. Read `audit-kit/RUN.md` completely before starting.
2. If the user passed arguments:
   - If it contains `no-update`, skip the update check step.
   - If it contains `fresh`, run every auditor of the Standard mode and skip the triage agent.
3. Follow all steps in `audit-kit/RUN.md` in order:
   - Prepare workspace and check project size.
   - Run triage check.
   - Launch auditors in parallel using `invoke_subagent` following `audit-kit/adapters/antigravity/subagents.md` (each with `TypeName: 'self'`, role, and `Prompt: 'audit-kit-agent: <name>...'`), ensuring isolated execution contexts without token or finding cross-contamination. If subagents are not supported, run sequentially with clean context rereads.
   - Verify Critical and High findings with the skeptic verifier (launching verifiers in parallel with `invoke_subagent`).
   - Deduplicate and re-score.
   - Produce `audit/AUDIT.md`, `audit/findings.json`, and update the Excel tracker if Python `openpyxl` is available.
