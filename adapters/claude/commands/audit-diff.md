---
description: Review the changes on this branch against a base branch (triage picks the auditors)
argument-hint: "[base branch]"
---
Run a Diff review by following the "Diff mode" section of `audit-kit/RUN.md` exactly. Base branch: $ARGUMENTS (if empty, let the triage agent find it). Launch the `audit-triage` subagent first, then each selected `*-auditor` subagent, in parallel where possible.
