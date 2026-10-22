# Updating audit-kit from the agent chat

Follow these steps when the user asks to check for or install a kit update. When `RUN.md` calls these steps before an audit, "stop" means stop the update check and carry on with the audit. This is not an audit: the read-only rules in `RULES.md` do not apply here, but never touch `audit/`.

Source: `https://raw.githubusercontent.com/victorfigueira/audit-kit/main/` (if the environment variable `AUDIT_KIT_REPO` points to another GitHub repository, use that owner and name instead).

1. **Read the installed version** from `audit-kit/VERSION` (treat a missing file as `0.0.0`).
2. **Read the latest version** with `curl -fsSL <source>VERSION`. If it fails, tell the user the check could not reach GitHub and stop.
3. **Compare.** If the installed version is the same or newer, say "audit-kit <version> is up to date" and stop.
4. **Show what is new.** Fetch `<source>CHANGELOG.md` and summarise, in the user's language, only the entries newer than the installed version (maximum 10 lines). Say whether the next audit will rerun every auditor: that happens only when the major version changes.
5. **Ask for confirmation** before installing. Do not continue without a clear yes.
6. **Install.** From the project root, run `curl -fsSL <source>get.sh | bash`. It replaces `audit-kit/`, refreshes the kit's own adapters and leaves `audit/` untouched.
7. **Report** in at most 5 lines: old and new version, and whether the IDE window needs reloading (yes if the installer printed any "added" or "updated" adapter lines).
