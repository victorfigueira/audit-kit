# Changelog

## 2.4.0 – 26/10/2026
- New Antigravity Skills adapter: modern `.agents/skills/<name>/SKILL.md` packages for `/audit`, `/audit-full`, `/audit-diff`, `/audit-jira`, and `/audit-check-update`, providing first-class slash commands and progressive disclosure in Google Antigravity.
- Legacy Antigravity `.agents/workflows/` are preserved for backward compatibility.
- New update check adapters: added explicit `/audit-check-update` commands for Claude Code, Antigravity, and Gemini CLI.
- `install.sh` automatically installs both modern skills and legacy workflows for Antigravity.

## 2.3.2 – 23/10/2026
- Fix: untracked files count as changed only when their hash differs from the previous audit (`untracked_hashes` in `findings.json`). Before, any untracked file reran the auditors on every incremental audit.
- Fix: auditors never audit the kit itself (its folders, the audit-kit sections of `AGENTS.md` and `CLAUDE.md`, and the installed adapters).
- Read-only inspection commands (`ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`) are allowed for every agent.

## 2.3.1 – 23/10/2026
- Fix: tokens are attributed to agents through a tag on the first line of every subagent prompt (`audit-kit-agent: <name>`) instead of keywords, which mislabelled verifier and triage runs as Security or Reliability. Keywords remain as a fallback, with corrected patterns.

## 2.3.0 – 23/10/2026
- New `tools/usage_report.py`: sums the tokens a Standard or Full audit consumed from Claude Code's session files, split by type (input, output, cache write, cache read) and by agent. Other tools show "not available"; figures are never estimated.
- Results go to `usage` in `findings.json`, a "Run data" section in `AUDIT.md`, the chat summary and a new Run log sheet in the tracker, which keeps one row per audit.
- `findings.json` records `run_type` (Fresh or Incremental).

## 2.2.1 – 23/10/2026
- Fix: `triage_check.py` treats a Critical or High finding as verified only if its verification is Confirmed, Downgraded, Inconclusive or Reinstated by user. Any other value sends it to the skeptic verifier.

## 2.2.0 – 23/10/2026
- Fix: the forced-run checks (kit major version, project context hash, tool and model, previous commit, 30-day rule, never-audited dimensions) now run in a script, `tools/triage_check.py`, whose result is binding. Before, the agent could skip them and carry over dimensions that had to run again.
- Fix: carried-over Critical and High findings that were never verified go to the skeptic verifier.
- Fix: `size_check.py` reads out-of-scope paths written as bullets under the "Out of scope paths" line.

## 2.1.0 – 22/10/2026
- New `tools/size_check.py`: measures the code in scope (git files, without binaries, lockfiles, `audit/`, `audit-kit/` and out-of-scope paths) and estimates its size in tokens at 4 characters per token.
- Standard and Full audits record the result as `code_size` in `findings.json` and in `AUDIT.md`. A fresh Full audit over the threshold asks before starting.
- Project context template: new "Size warning threshold" field.

## 2.0.0 – 22/10/2026
- New skeptic verifier (red team) between the auditors and the manager. It receives each Critical and High finding on its own and tries to prove it is a false positive from the surrounding code. Rejected findings leave `findings.json`, the tracker and the score; downgraded ones keep the lower severity.
- Verdicts in `audit/verification.md` (or `audit/diff/verification.md`); rejected findings listed in `AUDIT.md`. "reinstate <ID>" brings a rejected finding back.
- Tracker: new Verification column and "False positive" status, excluded from the Summary totals.
- Major version because it changes which findings count: the first audit after updating reruns every auditor.

## 1.7.0 – 22/10/2026
- Each audit records the tool and model (`findings.json`, `AUDIT.md`, tracker, chat summary). Carried-over dimensions keep the tool and model of their last real run.
- Incremental runs force every auditor when the tool or model changes, so scores from different models are not mixed. Audits without this information do not trigger the rule.
- User guide: new section on using more than one tool.

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
