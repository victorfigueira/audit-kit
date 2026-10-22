# Audit manager – how to run an audit

You are the audit manager. Any agent tool can follow this file. Read it fully before starting.

## Modes

| Mode | Auditors | When to use |
|---|---|---|
| Standard | maintainability, oss-health, architecture, security, reliability | Routine checks, before releases |
| Full | all ten files in `audit-kit/agents/` | Quarterly, before go-live, new project onboarding |

If the user did not say which mode, use Standard.

## Steps

1. **Prepare.** Create `audit/` at the project root if missing. If `audit/project-context.md` does not exist, copy `audit-kit/templates/project-context.md` there, fill it in from the README, package files and folder structure, mark doubts as TO CONFIRM, and tell the user before continuing. Record the current branch and short commit hash.
2. **Run the auditors.** For each auditor in the selected mode, follow its file in `audit-kit/agents/` together with `audit-kit/RULES.md`.
   - If your tool supports subagents or parallel agents, run one per auditor, in parallel, each in its own context.
   - If it does not, run them one after another and start each with a fresh reading of its file, so findings do not leak between dimensions.
   - Each auditor writes only its own report in `audit/`.
3. **Check.** Confirm every expected report exists and follows the template. Rerun a failed auditor once; if it fails again, mark that dimension "Not completed".
4. **Deduplicate.** When two reports describe the same root cause, keep the finding in the most relevant dimension and mention the other ID under cross-cutting themes.
5. **Write `audit/AUDIT.md`** using `audit-kit/templates/AUDIT.md`. The overall score is the average of the dimensions that were run, to one decimal. Dimensions not run show "Not audited".
6. **Write `audit/findings.json`** with this structure:
   ```json
   {
     "project": "name", "branch": "main", "commit": "abc1234",
     "date": "YYYY-MM-DD", "mode": "Standard",
     "scores": {"Security": 6, "Reliability": 7},
     "findings": [
       {"id": "SEC-001", "dimension": "Security", "severity": "High",
        "title": "Short title", "location": "src/file.ts:42",
        "recommendation": "Concrete fix", "effort": "S"}
     ]
   }
   ```
   Dimension names must match the table in `audit-kit/RULES.md` exactly.
7. **Update the tracker.** Run `python3 audit-kit/tools/generate_tracker.py`. It reads `audit/findings.json` and creates or updates `audit/audit-tracker.xlsx`, keeping Status, Owner, dates, Jira key and Notes from earlier runs. If Python or `openpyxl` is missing, do not install anything: tell the user to run `pip3 install openpyxl` and skip this step.
8. **Report in chat** (maximum 15 lines, in the user's language):
   ```
   Audit complete · Mode: <Standard|Full>
   Overall score: <x.x>/10
   <Dimension>: <score>   (one line each)
   Critical: <n> · High: <n>
   Files: audit/AUDIT.md · audit/audit-tracker.xlsx
   ```

## Optional: Jira tickets
After an audit, the user can ask for tickets. Follow `audit-kit/JIRA.md`.
