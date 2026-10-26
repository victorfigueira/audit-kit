# Changelog

## 2.11.3 – 26/10/2026
- Added visual Mermaid architecture diagram and comprehensive Roles Breakdown for the Audit Team in `README.md`.
- Synchronized documentation version references to `v2.11.3`.

## 2.11.2 – 26/10/2026
- Silent Batch CVSS v3.1 Calculation: added automated in-memory finding enrichment in `tools/generate_dashboard.py` and `tools/cvss.py`, eliminating repetitive individual CLI executions per finding.
- Security Auditor Workflow Refinement: updated `agents/security.md` to explicitly forbid executing shell commands per finding, avoiding disruptive terminal permission prompts.
- Batch CLI Support in `tools/cvss.py`: added `--file` and direct JSON file argument support to enrich findings files in a single pass.
- Resilient Vector Extraction: regex and multi-field vector extraction in `tools/cvss.py` to support raw strings, structured objects, and inline finding annotations.

## 2.11.1 – 26/10/2026
- Fixed shell variable parameter expansion bug where unquoted shell heredocs or echoes expanded `$0` in `$0.11` to `zsh.11` and `$3`/`$15` in pricing labels to empty strings.
- Added resilient numeric cost parsing and formatting in `templates/dashboard.html` that extracts numeric `total_usd` and formats `$X.XX`.
- Removed raw shell parameter signs from model pricing labels in `tools/usage_report.py`.
- Added shell quoting guidance in `RUN.md` Step 8.

## 2.11.0 – 26/10/2026
- CVSS v3.1 Security Scoring Engine: implemented FIRST.org official mathematical specification for CVSS v3.1 Base Score calculation, vector validation, and serialization in `tools/cvss.py`.
- Security Auditor & Skeptic Verifier Specifications: updated `agents/security.md` to compute CVSS vectors per finding and `agents/skeptic-verifier.md` to challenge vector metrics (AV, PR, AC).
- Interactive Dashboard Badges: rendered colored CVSS pills and vector tooltips in `audit/dashboard.html` for all security findings.
- Comprehensive Test Suite: added FIRST.org reference vector tests in `tools/test_cvss.py`.

## 2.10.0 – 26/10/2026
- Automated Audit Cost Calculation: added pricing matrix for Anthropic (Claude Opus, Sonnet, Haiku), Google Gemini (Pro, Flash), and OpenAI (GPT-4o, o1, o3-mini) with automatic USD cost calculation for input, output, and cache tokens in `tools/usage_report.py`.
- Financial Metrics in Dashboard: added dedicated Audit Cost card in `templates/dashboard.html` and cost history tracking across snapshots.
- One-Click Dashboard Access: updated `RUN.md` reporting step to deliver an immediate, clickable `file://` link to `dashboard.html` in chat upon audit completion.
- Updated report templates and documentation to reflect token costs and financial metrics.

## 2.9.0 – 26/10/2026
- Historical Audit Snapshots: automatically archive previous audits into `audit/snapshots/<timestamp>_<commit>/` before fresh or incremental runs via `tools/snapshot.py`.
- Audit Comparison & Diff Engine: `tools/snapshot.py compare` compares runs to report resolved findings, new findings, persistent findings, and dimension score deltas.
- Standalone Interactive HTML Dashboard: `tools/generate_dashboard.py` generates self-contained `audit/dashboard.html` with zero external dependencies, file:// compatibility, executive score cards, searchable/filterable findings explorer, and historical timeline diffing.
- New Command & Skill: added `/audit-dashboard` for Claude Code, Antigravity, Gemini CLI, Cursor, Windsurf, and Copilot.
- Integrated snapshot archiving and dashboard generation into `RUN.md` pipeline steps 1 and 10.

## 2.8.1 – 26/10/2026
- Refined and completed `docs/GUIDE.md` documentation for modern multi-environment adapters (Cursor, Windsurf, GitHub Copilot) and deterministic token estimation fallback (`tools/usage_report.py --estimate`).
- Updated adapter preservation guidelines and tool references across all supported environments.

## 2.8.0 – 26/10/2026
- New AI IDE adapters: added support and dedicated rule packages for Cursor (`.cursorrules`, `.cursor/rules/audit.mdc`), Windsurf (`.windsurfrules`), and GitHub Copilot (`.github/copilot-instructions.md`).
- Multi-target installation options updated for `cursor`, `windsurf`, and `copilot`.
- Completed Phase 4 (Expansion to Other AI Environments) — achieving 100% universal first-class AI support across all major coding agents.

## 2.7.2 – 26/10/2026
- Multi-target options in `install.sh` and `get.sh`: added CLI flag parsing (`--target`, `-h/--help`, `auto` discovery).
- Automatic legacy `.agent/` to `.agents/` directory migration in `install.sh`.
- Completed Phase 3 (Orchestrator & Installer Standardization).

## 2.7.1 – 26/10/2026
- Universal subagent dispatch protocol in `RUN.md`: formalized explicit execution strategies for Claude Code, Antigravity, and single-threaded sequential agents.

## 2.7.0 – 26/10/2026
- Deterministic token estimation fallback in `tools/usage_report.py`: calculates model-neutral token estimates (4 chars/token) from code in scope and audit report outputs when native session logs are absent.
- Added `--estimate` and `--no-fallback` CLI options.
- Completed Phase 2 (Agnostic Token Telemetry).

## 2.6.0 – 26/10/2026
- Cross-platform token telemetry in `tools/usage_report.py`: added native parser for Antigravity conversation transcripts and subagent logs (`transcript.jsonl`).
- Auto-engine detection between Claude Code and Antigravity via environment inspection and project discovery.
- Subagent token attribution via `invoke_subagent` conversation logs and `audit-kit-agent:` prompt tags.

## 2.5.1 – 26/10/2026
- Standardized Antigravity rules injection: added modular `adapters/antigravity/rules/audit-rules.md` deployed to `.agents/rules/` on install.
- `install.sh` automatically updates `GEMINI.md` when present, ensuring automatic rule discovery in Antigravity workspaces.
- Completed Phase 1 (Antigravity Full Parity & Modernization).

## 2.5.0 – 26/10/2026
- Native Antigravity parallel subagents: added `adapters/antigravity/subagents.md` defining concurrent auditor and skeptic verifier execution via `invoke_subagent`.
- Antigravity skills (`audit`, `audit-full`, `audit-diff`) and `RUN.md` now orchestrate auditors in parallel isolated contexts, eliminating context leakage between dimensions.
- Updated user guide with Antigravity subagent capabilities.

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
