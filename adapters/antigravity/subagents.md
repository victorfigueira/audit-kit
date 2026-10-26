# Antigravity Subagents Guide for audit-kit

This guide defines how Google Antigravity launches parallel subagents during an audit to ensure complete context isolation and high performance.

---

## Architecture

In Antigravity, the Audit Manager runs in the primary session and coordinates the audit by invoking subagents using the native `invoke_subagent` tool.

```
                    ┌────────────────────────┐
                    │     Audit Manager      │
                    │   (RUN.md in primary)  │
                    └───────────┬────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  Maintainer   │       │   Security    │       │  Reliability  │
│   Subagent    │       │   Subagent    │       │   Subagent    │
│ (invoke_self) │       │ (invoke_self) │       │ (invoke_self) │
└───────┬───────┘       └───────┬───────┘       └───────┬───────┘
        │                       │                       │
        ▼                       ▼                       ▼
audit/maintainability.md audit/security.md      audit/reliability.md
```

Each subagent:
1. Runs in an isolated turn/context (no token or finding leakage from other dimensions).
2. Has its prompt prefixed with `audit-kit-agent: <name>` (mandatory for token usage tracking in `tools/usage_report.py`).
3. Reads only its designated instructions (`audit-kit/agents/<name>.md`), shared rules (`audit-kit/RULES.md`), and project context (`audit/project-context.md`).
4. On incremental runs, reads its previous report (`audit/<name>.md`) to maintain stable finding IDs.
5. Writes only its own report to `audit/<name>.md` (or `audit/diff/<name>.md` in Diff mode).
6. Never modifies project source files (strictly read-only).

---

## Dispatching Auditors (Step 3 of RUN.md)

The Audit Manager invokes active auditors concurrently in a single turn using `invoke_subagent`:

```python
invoke_subagent(
    TypeName="self",
    Role="<Dimension> Auditor",
    Prompt="""audit-kit-agent: <name>

You are the <Dimension> auditor for this code audit.
1. Read audit-kit/RULES.md and audit-kit/agents/<name>.md.
2. Read audit/project-context.md to understand the scope and stack.
3. If audit/<name>.md exists from a previous run, read it to reuse existing finding IDs for persistent issues and sequence new IDs after the highest existing ID.
4. Conduct your analysis strictly in read-only mode.
5. Write your findings and score exclusively to audit/<name>.md using the template specified in audit-kit/templates/report.md.
6. Do not modify any codebase files.""",
    Workspace="inherit"
)
```

### Standard Mode Auditor Matrix

| Auditor | Role | Prompt Tag | Dimension File | Report Output |
|---|---|---|---|---|
| Maintainability | `Maintainability Auditor` | `audit-kit-agent: maintainability` | `audit-kit/agents/maintainability.md` | `audit/maintainability.md` |
| OSS Health | `OSS Health Auditor` | `audit-kit-agent: oss-health` | `audit-kit/agents/oss-health.md` | `audit/oss-health.md` |
| Architecture | `Architecture Auditor` | `audit-kit-agent: architecture` | `audit-kit/agents/architecture.md` | `audit/architecture.md` |
| Security | `Security Auditor` | `audit-kit-agent: security` | `audit-kit/agents/security.md` | `audit/security.md` |
| Reliability | `Reliability Auditor` | `audit-kit-agent: reliability` | `audit-kit/agents/reliability.md` | `audit/reliability.md` |

### Full Mode Additional Auditors

| Auditor | Role | Prompt Tag | Dimension File | Report Output |
|---|---|---|---|---|
| Performance | `Performance Auditor` | `audit-kit-agent: performance-scalability` | `audit-kit/agents/performance-scalability.md` | `audit/performance-scalability.md` |
| Testing & QA | `Testing QA Auditor` | `audit-kit-agent: testing-qa` | `audit-kit/agents/testing-qa.md` | `audit/testing-qa.md` |
| Observability | `Observability Auditor` | `audit-kit-agent: observability-operability` | `audit-kit/agents/observability-operability.md` | `audit/observability-operability.md` |
| Data Privacy | `Privacy Auditor` | `audit-kit-agent: data-privacy` | `audit-kit/agents/data-privacy.md` | `audit/data-privacy.md` |
| Infra & Cloud | `Infra CI/CD Auditor` | `audit-kit-agent: infra-cicd-cost` | `audit-kit/agents/infra-cicd-cost.md` | `audit/infra-cicd-cost.md` |

---

## Dispatching the Skeptic Verifier (Step 5 of RUN.md)

For every Critical and High finding, the manager dispatches independent skeptic verifiers in parallel:

```python
invoke_subagent(
    TypeName="self",
    Role="Skeptic Verifier",
    Prompt="""audit-kit-agent: skeptic-verifier

You are the Skeptic Verifier (independent red team).
Read and follow `audit-kit/agents/skeptic-verifier.md` exactly.

Finding to evaluate:
- ID: <FINDING_ID>
- Title: <TITLE>
- Severity: <SEVERITY>
- Location: <LOCATION>
- Evidence: <EVIDENCE>
- Impact: <IMPACT>

Inspect the surrounding codebase in read-only mode to determine whether this finding is a true issue or a false positive.
Return your structured verdict block (Confirmed, Downgraded, Rejected, or Inconclusive) with rationale and evidence.""",
    Workspace="inherit"
)
```

---

## Dispatching the Triage Agent (Step 2 of RUN.md / Diff Mode)

When running an incremental audit or diff review:

```python
invoke_subagent(
    TypeName="self",
    Role="Audit Triage",
    Prompt="""audit-kit-agent: triage

You are the Audit Triage agent.
Read and follow `audit-kit/agents/triage.md` exactly.
Determine which dimensions must run based on changes and write the triage plan to `audit/triage.md` (or `audit/diff/triage.md`).""",
    Workspace="inherit"
)
```
