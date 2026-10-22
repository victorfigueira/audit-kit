# Shared rules for every auditor

These rules apply to every agent in this kit, whatever tool runs it.

## Read-only
- Read code, configuration, dependencies, docs, CI files and git history.
- Write only inside the `audit/` folder at the project root.
- Never modify project files, install packages, start servers, connect to databases or cloud accounts, or push to git.
- Shell commands are allowed only where an agent file lists them explicitly.

## Context
- Before starting, read `audit/project-context.md`, the README and the main configuration files.
- Skip paths listed as out of scope in the project context (generated code, vendor folders, build output).

## Evidence
- Every finding cites a location (`file:line`, or file and section).
- Explain why it matters, not only what is wrong.
- Prefer fewer, well-evidenced findings over long lists. Merge findings with the same root cause.
- Only the repository counts as evidence. Information from memory, saved notes, earlier sessions or general knowledge about the project cannot support a finding on its own. List it under "To verify" in the report, with the exact check that would confirm or rule it out (for example a command the user can run).
- "To verify" items never get an ID, a severity or a place in the score. They become findings only when the user confirms them.

## Verification
- Every Critical and High finding is challenged by the skeptic verifier, which tries to prove it is a false positive by reading the surrounding code. Findings it rejects do not count.
- Write findings so they can survive that check: exact location, the code path that leads to the problem, and why existing guards do not stop it.

## Sensitive data
- Mask secrets: show at most the first 4 characters (for example `sk_l****`).
- Never copy real personal data (names, emails, IPs, IDs). Describe the field and its location instead.

## Boundaries
- Stay inside your dimension. If you notice something that belongs elsewhere, add one line under "Notes for other auditors" instead of a finding.

## Language
- All output (reports, findings, tickets, commit messages) is in English, whatever language the user chats in.

## Severity scale

| Severity | Meaning | Typical response |
|---|---|---|
| Critical | Exploitable, data loss, legal exposure or outage likely | Fix immediately |
| High | Serious risk or blocker; likely to cause incidents | Fix this sprint |
| Medium | Real issue with limited impact or a workaround | Plan this quarter |
| Low | Improvement or hygiene | Backlog |

## Scoring (per dimension, 1 to 10)

| Score | Meaning |
|---|---|
| 9–10 | Exemplary, no High or Critical findings |
| 7–8 | Solid, a few Medium issues |
| 5–6 | Acceptable with clear gaps, at least one High |
| 3–4 | Weak, several High or one Critical |
| 1–2 | Severe, multiple Critical findings |

## Finding IDs

`<PREFIX>-<NNN>`, numbered from 001 within each dimension (for example `SEC-001`).

| Dimension | Prefix | Report file |
|---|---|---|
| Maintainability | MNT | audit/maintainability.md |
| Open Source Health | OSS | audit/oss-health.md |
| Architecture | ARC | audit/architecture.md |
| Security | SEC | audit/security.md |
| Reliability | REL | audit/reliability.md |
| Performance and Scalability | PRF | audit/performance-scalability.md |
| Testing and QA | TST | audit/testing-qa.md |
| Observability and Operability | OBS | audit/observability-operability.md |
| Data and Privacy Compliance | PRV | audit/data-privacy.md |
| Infra, CI/CD and Cloud Cost | INF | audit/infra-cicd-cost.md |

Each report follows `audit-kit/templates/dimension-report.md`.
