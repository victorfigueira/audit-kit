# audit-kit

A portable code audit team: ten read-only auditors and a manager that consolidates their reports into a scored summary, an Excel tracker and, optionally, Jira tickets.

Drop this folder into the root of any project. It works with Claude Code, Antigravity (Gemini), Gemini CLI or any agent that can read files.

## Set up a new project

### 1. Install the kit

From the root of the project you want to audit:

```
curl -fsSL https://raw.githubusercontent.com/victorfigueira/audit-kit/main/get.sh | bash
```

This downloads the kit into `audit-kit/` and installs the commands for Claude Code, Antigravity and Gemini CLI. For one tool only, add its name at the end: `| bash -s -- antigravity` (or `claude`, `gemini`). To pin a version, put `AUDIT_KIT_REF=v1.1.0` before `bash`.

If the project repository is public, keep the reports and the kit copy out of git:

```
echo "audit/" >> .gitignore
echo "audit-kit/" >> .gitignore
```

### 2. Fill in the project context

Reload the IDE window, then paste this into the agent chat:

```
Fill in audit/project-context.md from the README, package.json, AGENTS.md and folder structure. Mark anything you are not sure about with TO CONFIRM. Add build output and dependency folders to the out of scope paths. In "Commands auditors may run", list only the existing test and lint scripts. Do not change any other file.
```

Review the file and resolve every TO CONFIRM by hand. This step has the biggest effect on audit quality.

### 3. Run the audit

| Tool | Standard | Full | Jira |
|---|---|---|---|
| Claude Code | `/audit` | `/audit-full` | `/audit-jira` |
| Antigravity | `/audit` | `/audit-full` | `/audit-jira` |
| Gemini CLI | `/audit` | `/audit-full` | `/audit-jira` |
| Any other agent | "Follow audit-kit/RUN.md, standard mode" | "Follow audit-kit/RUN.md, full mode" | "Follow audit-kit/JIRA.md" |

### Update the kit in a project

Run the same `curl` command again. It replaces `audit-kit/` and keeps `audit/` (context, reports and tracker).

### Private repository or no curl

With the GitHub CLI:

```
gh api repos/victorfigueira/audit-kit/contents/get.sh -H "Accept: application/vnd.github.raw" | AUDIT_KIT_REPO=git@github.com:victorfigueira/audit-kit.git bash
```

Or manually: copy the `audit-kit/` folder into the project root and run `bash audit-kit/install.sh`.

## What you get

All outputs go to `audit/` in the project:

- `<dimension>.md`: one report per auditor.
- `AUDIT.md`: executive summary, scores and priorities.
- `findings.json`: consolidated findings (input for the tracker).
- `audit-tracker.xlsx`: Summary, Findings and Legend sheets. Your Status, Owner, dates, Jira key and Notes are kept across runs.
- `jira-proposal.md`: only when you run the Jira workflow.

## Modes

- **Standard** (5 auditors): Maintainability, Open Source Health, Architecture, Security, Reliability.
- **Full** (10 auditors): the five above plus Performance and Scalability, Testing and QA, Observability and Operability, Data and Privacy Compliance, Infra, CI/CD and Cloud Cost.

## Folder contents

| Path | Purpose |
|---|---|
| `RUN.md` | Manager instructions: the orchestration. Start here. |
| `RULES.md` | Shared rules, severity scale, scoring, finding IDs. |
| `agents/` | One definition per auditor (tool-agnostic). |
| `templates/` | Report, summary and project context templates. |
| `JIRA.md` | Optional ticket workflow. |
| `tools/generate_tracker.py` | Builds the Excel tracker (needs Python 3 and `openpyxl`). |
| `adapters/` | Thin wrappers for each tool; copied by `install.sh`. |
| `install.sh` | Installs the adapters into the project. |

## Where the adapters go

| Tool | Files created |
|---|---|
| All | `AGENTS.md` (shared rules section), `audit/project-context.md` |
| Claude Code | `.claude/agents/*-auditor.md`, `.claude/commands/*.md`, section in `CLAUDE.md` |
| Antigravity | `.agents/workflows/*.md` (older versions used `.agent/`; both are read) |
| Gemini CLI | `.gemini/commands/*.toml` |

Adapters only point to the files in this folder. To change how an auditor works, edit `agents/<name>.md` here, never the adapter.

## Updating

Replace the `audit-kit/` folder with the new version. Adapters do not need reinstalling unless the changelog says so. `install.sh` never overwrites existing files; to refresh an adapter, delete it and run the script again.

## Projects with an older audit setup

If the project already has auditors or commands with the same names (for example `.claude/agents/security-auditor.md` or `.claude/commands/audit.md`), `install.sh` skips them. Delete or rename the old files first, then run the script.

## Requirements

- Python 3 and `openpyxl` for the tracker (`pip3 install openpyxl`). Without them the audit still runs; only the Excel step is skipped.
- For Jira: the Atlassian Rovo MCP Server or a Jira API token in an environment variable.

## Safety

Auditors are read-only by instruction. Tools that support it (Claude Code) also restrict them to the tools in each adapter. Real cloud, database or production access is never part of the audit.
