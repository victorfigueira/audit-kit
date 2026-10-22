# Audit manager – how to run an audit

You are the audit manager. Any agent tool can follow this file. Read it fully before starting.

## Before any audit: update check

Applies to every mode, including Diff. Skip it only if the user wrote "no-update" with the command.

1. Follow steps 1 to 3 of `audit-kit/UPDATE.md` (installed version, latest version, compare). If GitHub cannot be reached, say so in one line and continue with the installed version.
2. If a newer version exists, follow steps 4 and 5 of `UPDATE.md`: summarise what is new and ask the user whether to update now. Wait for the answer.
3. If the user says yes, finish `UPDATE.md` (install and report), then read this file again from the start, because it may have changed, and continue with the audit the user asked for. Skip the update check on this second reading. If the update added new subagent definitions that the current session cannot load yet, run those auditors by following their files in `audit-kit/agents/` instead.
4. If the user says no, continue with the installed version.

## Modes

| Mode | Auditors | When to use |
|---|---|---|
| Standard | maintainability, oss-health, architecture, security, reliability | Routine checks, before releases |
| Full | all ten files in `audit-kit/agents/` | Quarterly, before go-live, new project onboarding |
| Diff | chosen by the triage agent from the ten | Before merging a branch or opening a pull request |

If the user did not say which mode, use Standard. Diff mode has its own steps (see "Diff mode" below).

## Incremental runs

Standard and Full are incremental when `audit/findings.json` exists: dimensions that the changes since the previous audit do not affect are carried over instead of audited again. The triage agent decides, following `audit-kit/agents/triage.md`. The run is fresh (every auditor of the mode runs) when there is no previous audit, when the user asks for a fresh audit (for example `/audit fresh`), or when the triage agent forces it. Use fresh runs for quarterly audits and before go-live.

## Steps

1. **Prepare.** Create `audit/` at the project root if missing. If `audit/project-context.md` does not exist, copy `audit-kit/templates/project-context.md` there, fill it in from the README, package files and folder structure, mark doubts as TO CONFIRM, and tell the user before continuing. Record the current branch, short commit hash, the kit version from `audit-kit/VERSION` and the SHA-256 hash of `audit/project-context.md` (`shasum -a 256`, or `sha256sum` where `shasum` is missing), and the tool and model running this audit (for example `Claude Code` and `claude-opus-5-5`, or `Antigravity` and the Gemini model selected). Write `unknown` for anything you cannot tell; never guess.
2. **Triage (incremental runs only).** If `audit/findings.json` exists and the user did not ask for a fresh audit, run the triage agent with `audit-kit/agents/triage.md` in Incremental mode, passing the tool and model recorded in step 1. It writes `audit/triage.md`. Show its plan table in chat and continue without waiting. Auditors marked Skip are carried over: do not run them, and keep their report in `audit/` untouched.
3. **Run the auditors.** For each auditor marked Run (or every auditor in the mode on a fresh run), follow its file in `audit-kit/agents/` together with `audit-kit/RULES.md`.
   - If your tool supports subagents or parallel agents, run one per auditor, in parallel, each in its own context.
   - If it does not, run them one after another and start each with a fresh reading of its file, so findings do not leak between dimensions.
   - Each auditor writes only its own report in `audit/`.
   - If the dimension has a previous report, the auditor reads it first and keeps the same ID for a finding that is still present, and numbers new findings after the highest previous ID. Fixed findings are listed under "Strengths" with their old ID. This keeps the tracker rows stable.
4. **Check.** Confirm every expected report exists and follows the template. Rerun a failed auditor once; if it fails again, mark that dimension "Not completed".
5. **Verify.** Send every Critical and High finding from the reports of this run to the skeptic verifier (`audit-kit/agents/skeptic-verifier.md`). Do not verify findings of carried-over dimensions; they keep the verdict recorded in `findings.json`. Do not verify findings the user reinstated earlier (verification "Reinstated by user").
   - Give the verifier only the finding: ID, title, severity, location, evidence and impact. Never the auditor's full report or other findings.
   - If your tool supports subagents, run one verifier per finding, in parallel; with more than 10 findings, group up to 5 from the same dimension per verifier. Otherwise verify them one after another, rereading the verifier file each time and setting aside what you concluded as manager.
   - Apply the verdicts: **Rejected** findings leave the findings list and the score; **Downgraded** findings take the new severity and keep the original in `original_severity`; **Confirmed** and **Inconclusive** findings stay as they are. Use any corrected location.
   - Write `audit/verification.md`: a summary line (checked, confirmed, downgraded, rejected, inconclusive) followed by every verdict block. Do not edit the auditors' reports.
   - If the user later disagrees with a rejection ("reinstate SEC-002"), move it back into the findings with verification "Reinstated by user", re-score, and rewrite `AUDIT.md`, `findings.json` and the tracker.
6. **Deduplicate and re-score.** When two reports describe the same root cause, keep the finding in the most relevant dimension and mention the other ID under cross-cutting themes. Then re-score every dimension that gained or lost a finding, or had one rejected or downgraded by the verifier, using the scale in `audit-kit/RULES.md`, and record each change under "Score adjustments" in `AUDIT.md` (auditor's score, final score, reason). Use the final scores everywhere else. Move any finding that rests only on memory or notes, not on the repository, to "To verify". Carried-over dimensions keep their score and findings unless a duplicate with a new finding forces a change, which you record under "Score adjustments".
7. **Write `audit/AUDIT.md`** using `audit-kit/templates/AUDIT.md`. The overall score is the average of the dimensions in the mode that were run or carried over, to one decimal. Dimensions never audited show "Not audited". Mark carried-over dimensions with the commit, date, tool and model of their last real run.
8. **Write `audit/findings.json`** with this structure:
   ```json
   {
     "project": "name", "branch": "main", "commit": "abc1234",
     "date": "YYYY-MM-DD", "mode": "Standard", "kit_version": "2.0.0",
     "context_hash": "<sha256 of audit/project-context.md>",
     "tool": "Claude Code", "model": "claude-opus-5-5",
     "scores": {"Security": 6, "Reliability": 7},
     "dimensions": {
       "Security": {"score": 6, "commit": "abc1234", "date": "YYYY-MM-DD", "tool": "Claude Code", "model": "claude-opus-5-5", "carried_over": false},
       "Reliability": {"score": 7, "commit": "9f8e7d6", "date": "YYYY-MM-DD", "tool": "Claude Code", "model": "claude-opus-5-5", "carried_over": true}
     },
     "findings": [
       {"id": "SEC-001", "dimension": "Security", "severity": "High",
        "title": "Short title", "location": "src/file.ts:42",
        "recommendation": "Concrete fix", "effort": "S",
        "verification": "Confirmed"}
     ],
     "rejected": [
       {"id": "ARC-002", "dimension": "Architecture", "title": "Short title",
        "location": "src/file.ts:10", "reason": "Guard at src/api.ts:31 blocks this path"}
     ]
   }
   ```
   Dimension names must match the table in `audit-kit/RULES.md` exactly. Use the final scores, and leave "To verify" items out.
   - Each finding has `verification`: `Confirmed`, `Downgraded`, `Inconclusive`, `Reinstated by user` or `Not checked` (Medium and Low). Downgraded findings also have `original_severity`. Carried-over findings keep theirs.
   - `rejected` lists the findings the verifier rejected in this run and those carried over from dimensions that did not run, each with `id`, `dimension`, `title`, `location` and `reason`. They never count in scores.
   - `context_hash` is the hash recorded in step 1, so the next run can tell whether the project context changed.
   - `commit` and `date` at the top are this run's. In `dimensions`, a dimension that ran gets this run's commit, date, tool and model; a carried-over dimension keeps those of its last real run, so the 30-day rule counts from the last real check.
   - Include the findings of carried-over dimensions, copied from the previous `findings.json`, so the tracker does not mark them "Not found in latest audit".
   - Keep entries in `dimensions` for dimensions outside the current mode that the previous file had (for example Full dimensions during a Standard run), but leave them out of `scores` and the overall score.
9. **Update the tracker.** Run `python3 audit-kit/tools/generate_tracker.py`. It reads `audit/findings.json` and creates or updates `audit/audit-tracker.xlsx`, keeping Status, Owner, dates, Jira key and Notes from earlier runs. If Python or `openpyxl` is missing, do not install anything: tell the user to run `pip3 install openpyxl` and skip this step.
10. **Report in chat** (maximum 15 lines, in the user's language):
   ```
   Audit complete · Mode: <Standard|Full> · <tool> / <model>
   Overall score: <x.x>/10
   <Dimension>: <score>   (one line each; add "carried over" where it applies)
   Critical: <n> · High: <n> · To verify: <n>
   Verifier: <checked> checked · <rejected> rejected · <downgraded> downgraded
   Files: audit/AUDIT.md · audit/audit-tracker.xlsx
   ```

## Diff mode

Reviews only what changed against a base branch. Outputs go to `audit/diff/` and never touch the main reports, `findings.json` or the tracker. Each Diff run replaces the previous contents of `audit/diff/`.

1. **Prepare.** As in Standard step 1, then empty `audit/diff/` (create it if missing).
2. **Triage.** Run the triage agent with `audit-kit/agents/triage.md`, passing the base branch if the user named one. It writes `audit/diff/triage.md`.
3. **Confirm the plan.** Show the plan table in chat (auditor, decision, reason) and wait for the user to confirm or change it. Skip this wait only if the user asked to go ahead without review. If triage skipped everyone, say so and stop.
4. **Run the auditors** marked Run, as in Standard step 3, with these changes for each auditor:
   - Review the files listed for it in the plan, reading other files only for context.
   - Report problems the change introduces or makes worse. Problems that already existed in untouched code go to "Out of scope / limitations" in one line.
   - Write the report to `audit/diff/<report file name>` instead of `audit/`.
   - Do not score: write "Score: Not scored (diff review)" instead of a number.
5. **Check, verify and deduplicate** as in Standard steps 4 to 6, without re-scoring. The verifier writes to `audit/diff/verification.md`, and the verdict uses the findings that survive.
6. **Write `audit/diff/DIFF-AUDIT.md`** using `audit-kit/templates/DIFF-AUDIT.md`. Verdict: "Block merge" if there is any Critical, "Fix before merge" if there is any High, otherwise "Ready to merge".
7. **Report in chat** (maximum 12 lines, in the user's language):
   ```
   Diff review complete · Base: <branch> · <tool> / <model>
   Verdict: <verdict>
   Reviewed: <dimensions> · Skipped: <n>
   Critical: <n> · High: <n> · Medium: <n> · Low: <n> · To verify: <n>
   File: audit/diff/DIFF-AUDIT.md
   ```

## Optional: Jira tickets
After an audit, the user can ask for tickets. Follow `audit-kit/JIRA.md`.
