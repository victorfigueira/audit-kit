# Audit Report – <project>

Mode: Standard | Full · Run: Fresh | Incremental · Kit: <version> · Tool: <tool> / <model> · Code: <files> files, <lines> lines, ~<tokens> tokens · Branch: <branch> · Commit: <short hash> · Date: <YYYY-MM-DD>

## Overall score: <x.x>/10

| Dimension | Score | Status | Critical | High | Medium | Low |
|---|---|---|---|---|---|---|
| <dimension> | <n>/10 or Not audited | Audited or Carried over (<commit>, <date>, <tool> / <model>) | | | | |

## Verification
Checked: <n> Critical and High · Confirmed: <n> · Downgraded: <n> · Rejected: <n> · Inconclusive: <n>. Details in `audit/verification.md`.

| Rejected | Title | Reason |
|---|---|---|
| <ID> | <title> | <counter-evidence in one line> |

To reinstate a rejected finding, tell the agent "reinstate <ID>".

## Executive summary
<5 to 8 sentences in plain language for a non-technical reader.>

## Top priorities
1. <ID> · <Title> · <Severity> · <one line on why>

## Cross-cutting themes
<Problems that appear in several dimensions, with the related IDs.>

## Quick wins
<High value, effort S.>

## To verify
<Items from all reports that need a check by the user before they count as findings, with the check for each.>

## Score adjustments
<Only if the manager changed a score: dimension, auditor's score, final score, reason.>

## Triage
<Incremental runs only: which dimensions were carried over and why, from audit/triage.md.>

## Comparison with previous audit
<Only if audit/audit-tracker.xlsx existed before this run: new, fixed and still open findings.>

## Run data
| Input | Output | Cache write | Cache read | Total | Cost (USD) | Source |
|---|---|---|---|---|---|---|
| <n> | <n> | <n> | <n> | <n> | ~$<x.xx> | Claude Code / Antigravity / Estimate |

Per agent: <one line per agent with its total, from usage.agents>.

## Limitations
<What the audit could not check.>
