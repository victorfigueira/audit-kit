# Changelog

## 1.6.2 – 22/10/2026
- User guide: sequence diagrams for the audit, Diff review and Jira interactions.

## 1.6.1 – 22/10/2026
- New user guide in `docs/GUIDE.md`, linked from the README.

## 1.6.0 – 22/10/2026
- Every audit (Standard, Full, Diff) checks for a newer kit version first, summarises it and offers to install it before starting. `no-update` skips the check. If GitHub cannot be reached, the audit continues with the installed version.

## 1.5.0 – 22/10/2026
- New `/audit-check-update` command: compares the installed version with the latest on GitHub, summarises the changes and runs the installer after confirmation (`UPDATE.md`).
- Incremental runs force every auditor only when the major version changes. From now on, changes to scoring or evidence rules bump the major version; new features and fixes do not force a full run.

## 1.4.1 – 22/10/2026
- Project context changes are detected with a SHA-256 hash stored in `findings.json` (`context_hash`) instead of git, so incremental runs work when `audit/` is in `.gitignore`.
- Audits from 1.4.0 have no hash: the first run after updating records it without forcing a full run.

## 1.4.0 – 22/10/2026
- Incremental runs: with a previous audit, `/audit` and `/audit-full` run the triage agent against the previous audit's commit and carry over unaffected dimensions (score, report and findings).
- Forced full reruns: `fresh` argument, kit major/minor version change, project context change, previous commit missing. Security and Open Source Health rerun after 30 days.
- `findings.json` records `kit_version` and, per dimension, the commit and date of its last real run.
- Rerun auditors keep the IDs of findings still present, so tracker rows stay stable.
- New `VERSION` file.
- `install.sh` refreshes the kit's own adapters (files that point to `audit-kit/`) and still skips anything else.
- Note: audits made before 1.4.0 have no kit version, so the first run after updating runs every auditor.

## 1.3.0 – 22/10/2026
- New Diff mode (`/audit-diff [base]`): a triage agent reads the changes against the base branch, picks the auditors and waits for confirmation.
- Diff reviews write to `audit/diff/` with a merge verdict instead of scores; they never touch the main reports or the tracker.
- Project context template has a "Default branch" field.
- Existing projects: re-run the installer to add the new command and agent (existing files are kept).

## 1.2.1 – 22/10/2026
- install.sh installs openpyxl when missing; a failure never stops the install.

## 1.2.0 – 22/10/2026
- Findings must rest on repository evidence; anything from memory or notes goes to a new "To verify" section.
- Manager re-scores dimensions after merging duplicates and records changes under "Score adjustments".

## 1.1.0 – 22/10/2026
- One-line installer (get.sh) that downloads the kit and runs install.sh.

## 1.0.0 – 22/10/2026
- Ten auditors, Standard and Full modes.
- Manager orchestration in RUN.md.
- Excel tracker generator that preserves manual columns.
- Optional Jira workflow.
- Adapters for Claude Code, Antigravity and Gemini CLI.
