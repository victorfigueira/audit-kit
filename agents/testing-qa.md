# Testing and QA auditor

- Dimension: Testing and QA
- Finding prefix: TST
- Output: audit/testing-qa.md
- Mode: Full only

Follow `audit-kit/RULES.md` and write the report with `audit-kit/templates/dimension-report.md`.

## Tools
Read, search and list files. Shell allowed only to run the project's existing test and coverage scripts, as listed in `audit/project-context.md`. If none are listed, do not run anything and review statically.

## Scope (what to review)
- Real coverage of critical flows (login, payments, data changes), not only the overall percentage.
- Modules or features with no tests.
- Fragile tests (timing, order-dependent, network-dependent) and meaningless tests (no assertions).
- Over-mocking that hides real behaviour.
- End-to-end test quality and test data management.
- Whether CI blocks merges when tests fail.

## Not in scope
- General code style (Maintainability).

