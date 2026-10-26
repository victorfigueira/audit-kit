# Antigravity Workspace Guidelines for audit-kit

## Language & Documentation Integrity
- All documentation, code comments, commit messages, and changelog entries must be written strictly in **English**, regardless of the conversation language with the user.

## Versioning & Release Conventions
Every functional change, feature, or bug fix must follow the project's established semantic versioning standard:

### 1. Version Semantics (`MAJOR.MINOR.PATCH`)
- **MAJOR (`X.0.0`)**: Breaking changes, modifications to scoring methodology, changes to evidence rules, or changes that invalidate prior findings (forces every auditor to rerun on incremental audits).
- **MINOR (`x.Y.0`)**: New features, new auditor dimensions, new adapters, new tools, or backwards-compatible capabilities.
- **PATCH (`x.y.Z`)**: Bug fixes, logic refinements, script improvements, and documentation updates.

### 2. Required Version Updates
Whenever a version is bumped, the following files must be updated together:
1. `VERSION`: Contains the raw version string (e.g. `2.4.0`).
2. `CHANGELOG.md`: Add a new release section at the top formatted as:
   ```markdown
   ## X.Y.Z – DD/MM/YYYY
   - Bullet points explaining the changes clearly and concisely.
   ```
3. `README.md`: Update the current version declaration on line 3:
   ```markdown
   Current version: **X.Y.Z** (see `CHANGELOG.md`).
   ```
   and update example pins like `AUDIT_KIT_REF=vX.Y.Z`.
4. `RUN.md`: Update version references in template examples if present.
5. `BACKLOG.md`: Update status or reference when corresponding tickets are completed.

### 3. Git Commit & Tagging Protocol
- **Commit format**: `vX.Y.Z: <concise description in English>` (e.g. `v2.4.0: add modern Antigravity skills adapter`).
- **Git Tag**: Tag the release with annotated tag `vX.Y.Z` (`git tag -a vX.Y.Z -m "vX.Y.Z: <summary>"`) and push tags to remote (`git push origin --tags`).
