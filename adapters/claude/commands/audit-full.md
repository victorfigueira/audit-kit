---
description: Run a Full code audit with the audit-kit team (incremental when a previous audit exists)
argument-hint: "[fresh]"
---
Run a Full audit by following `audit-kit/RUN.md` exactly. Arguments: $ARGUMENTS (if it says "fresh", run every auditor and skip triage). Launch the `audit-triage` subagent first when RUN.md calls for it, then each `*-auditor` subagent to run, in parallel where possible.
