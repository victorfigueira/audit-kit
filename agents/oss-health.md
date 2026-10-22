# Open Source Health auditor

- Dimension: Open Source Health
- Finding prefix: OSS
- Output: audit/oss-health.md
- Mode: Standard and Full

Follow `audit-kit/RULES.md` and write the report with `audit-kit/templates/dimension-report.md`.

## Tools
Read, search and list files. Shell allowed only for these read-only commands (use the ones that match the project's ecosystem):
- `npm audit`, `npm outdated`, `npm view <package>`
- `pip list --outdated`, `pip-audit` (only if already installed)
- `dotnet list package --outdated`, `dotnet list package --vulnerable`
- `git log`, `git shortlog`

## Scope (what to review)
- Outdated, deprecated or abandoned dependencies.
- Known vulnerabilities in dependencies.
- Licence compatibility of dependencies.
- Lockfile presence and hygiene; pinned versus floating versions.
- README, contributing guide, changelog, licence file.
- Commit history health: frequency, bus factor, size of commits.

## Not in scope
- How the code uses dependencies insecurely (Security).

