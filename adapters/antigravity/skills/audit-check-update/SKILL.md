---
name: audit-check-update
description: >-
  Check if a newer version of audit-kit is available on GitHub, display release notes, and install updates upon confirmation.
---

# Check audit-kit Updates

Check for new releases of audit-kit and install them safely into the project.

## Procedure
1. Follow `audit-kit/UPDATE.md` step-by-step.
2. Read the installed version from `audit-kit/VERSION`.
3. Fetch the latest release version and changelog from GitHub (`https://raw.githubusercontent.com/victorfigueira/audit-kit/main/`).
4. If an update exists:
   - Summarise the new features and fixes concisely in the user's language.
   - Note if a major version bump forces a full rerun on the next audit.
   - Ask the user for confirmation before executing the update installer.
5. If confirmed, execute the installer script, leaving the `audit/` folder untouched.
