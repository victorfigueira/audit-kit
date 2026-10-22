---
description: Review the changes on this branch against a base branch (triage picks the auditors)
argument-hint: "[base branch] [no-update]"
---
Run a Diff review by following the "Diff mode" section of `audit-kit/RUN.md` exactly. Arguments: $ARGUMENTS. "no-update" skips the update check; any other word is the base branch (if none, let the triage agent find it). Launch the `audit-triage` subagent first, then each selected `*-auditor` subagent, in parallel where possible.
