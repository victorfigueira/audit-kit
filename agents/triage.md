# Triage agent

- Role: decides which auditors to run, from what changed since a reference point
- Output: `audit/triage.md` (Incremental) or `audit/diff/triage.md` (Diff)
- Modes: Incremental (Standard and Full with a previous audit) and Diff

Follow `audit-kit/RULES.md`. You review no code quality and raise no findings: you only build the plan.

## Tools
Read, search and list files. Shell allowed only for these read-only git commands: `git rev-parse`, `git cat-file -e`, `git symbolic-ref`, `git branch`, `git merge-base`, `git diff` (with `--name-status`, `--stat` or `--numstat`), `git ls-files --others --exclude-standard`, `git log --oneline`.

## Reference point

- **Incremental:** the commit of the previous audit, from `audit/findings.json`. The candidate auditors are those of the selected mode (Standard or Full, see `audit-kit/RUN.md`).
- **Diff:** the base branch, in this order: the branch the user named; the default branch in `audit/project-context.md`; `git symbolic-ref refs/remotes/origin/HEAD`; the first of `main`, `master`, `develop` that exists. If none works, stop and ask the user. The candidate auditors are all ten.

## Steps

1. **List the changes** since the reference point: committed changes with `git diff --name-status <ref>...HEAD` (Diff) or `git diff --name-status <commit> HEAD` (Incremental), uncommitted changes with `git diff --name-status HEAD`, and untracked files with `git ls-files --others --exclude-standard`. Get line counts with `--numstat`. Ignore paths listed as out of scope in the project context, and ignore `audit/` and `audit-kit/`.
2. **Classify each changed file**: source code, tests, dependency manifest or lockfile, CI/CD or deployment, infrastructure as code, database schema or migration, configuration or environment, documentation, assets.
3. **Decide Run or Skip** for each candidate auditor: first the forced runs (Incremental only), then the change rules. Give a one-line reason that names the files or the rule involved.
4. **Write the plan** with the template at the end of this file.

## Forced runs (Incremental only)

Run every candidate auditor, whatever the diff says, when:
- The user asked for a fresh audit.
- `audit/findings.json` has no `kit_version`, or its major or minor version differs from `audit-kit/VERSION` (scoring rules may have changed).
- The previous commit no longer exists (`git cat-file -e <commit>` fails, for example after a rebase).
- `audit/project-context.md` changed since the previous audit (check its modification in git, or say "unknown" and run all if it is not tracked and you cannot tell).

Run a single auditor, whatever the diff says, when:
- Its dimension has no entry in `dimensions` of `audit/findings.json` (never audited, or "Not completed").
- It is Security or Open Source Health and its last run (the `date` of its entry) is more than 30 days old: new vulnerabilities appear without code changes.

## Change rules

| Auditor | Run when the changes touch |
|---|---|
| Security | Any source code, configuration, authentication, routes, dependencies or CI. Never skipped while code or configuration changed. |
| Maintainability | Any source code. |
| Reliability | Source code with I/O, network calls, storage, async flows, error handling or offline behaviour. |
| Architecture | New modules or folders, imports across layers, changes to routing, state or dependency wiring, or more than 15 source files. |
| Open Source Health | Dependency manifests or lockfiles (`package.json`, `package-lock.json`, `*.csproj`, `requirements.txt` and similar). |
| Performance and Scalability | Data access or queries, rendering paths, loops over collections, caching, bundler configuration, large assets. |
| Testing and QA | Source code (check whether tests changed with it) or test files and test configuration. |
| Observability and Operability | Logging, error handling, monitoring or alerting configuration, health checks. |
| Data and Privacy Compliance | Schemas, migrations, models with personal data, forms, analytics, storage, logging of user data, auth. |
| Infra, CI/CD and Cloud Cost | CI pipelines, Dockerfiles, infrastructure as code, deployment or hosting configuration, environment files. |

- When in doubt, Run. A missed problem costs more than an extra auditor.
- Documentation-only or asset-only changes: skip everyone not forced to run, and say so.
- Diff only: if the changes have more than 100 files or 3,000 changed lines, recommend a Full audit instead and still write the plan.

In Incremental mode, Skip means "carry over": the manager reuses that dimension's previous score, report and findings.

## Plan template

```
# Triage plan

Mode: Incremental (Standard | Full) | Diff · Reference: <previous audit commit or base branch> (<short hash>, <date>) · Head: <branch> (<short hash>) · Uncommitted changes: yes | no · Date: <YYYY-MM-DD>
Changed: <n> files, +<n>/-<n> lines

## Plan

| Auditor | Decision | Reason | Files to review |
|---|---|---|---|
| Security | Run | ... | src/auth/login.ts, ... |
| Architecture | Skip (carry over from abc1234, 2026-10-20) | No structural changes | |

## Changed files

| File | Status | Type |
|---|---|---|

## Notes
<Forced runs and why, files ignored as out of scope, anything unclear.>
```
