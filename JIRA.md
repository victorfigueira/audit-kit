# Jira ticket workflow

Run only when the user asks for it, after an audit exists.

## Connection
- Preferred: the Atlassian Rovo MCP Server (`https://mcp.atlassian.com/v1/mcp/authv2`), signed in as the user.
- Alternative: Jira REST API with a token read from an environment variable (`JIRA_API_TOKEN`). Never write tokens into any file.
- If neither is available, stop after step 4 and tell the user.

## Steps
1. Read `audit/AUDIT.md`, `audit/findings.json`, `audit/project-context.md` and `audit/audit-tracker.xlsx`.
2. Select all Critical and High findings with status Open, plus Medium ones that block other work. Group findings with the same root cause into one ticket. Maximum 15 tickets.
3. Search Jira for open issues on the same topic. Skip duplicates and record the existing key.
4. Write `audit/jira-proposal.md`: for each ticket give summary, description, acceptance criteria, priority, labels (`audit` plus the dimension) and the finding IDs it covers. Use the project key and issue type from the project context; ask the user if they are missing. Then **stop and ask the user to approve, edit or drop tickets.**
5. After approval, create only the approved tickets and write each key into the Jira key column of the Findings sheet in `audit/audit-tracker.xlsx`.

## Rules
- Never include secrets or personal data in tickets. For security findings, give file and line only.
- All ticket text in English.
