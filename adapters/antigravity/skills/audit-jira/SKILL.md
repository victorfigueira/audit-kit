---
name: audit-jira
description: >-
  Propose and create Jira tickets from findings recorded in the latest audit-kit run.
---

# Jira Workflow

Convert audit findings into structured Jira issues or user stories.

## Procedure
1. Follow `audit-kit/JIRA.md` exactly.
2. Read the latest findings from `audit/findings.json` and `audit/AUDIT.md`.
3. Filter findings based on user requirements or focus areas.
4. Generate `audit/jira-proposal.md` proposing issue types, summaries, descriptions, and priorities.
5. **STOP** and wait for explicit user approval before calling Jira MCP tools or Jira API endpoints to create any tickets.
