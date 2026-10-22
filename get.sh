#!/usr/bin/env bash
# One-line installer for audit-kit.
# Run it from inside the project you want to audit:
#   curl -fsSL https://raw.githubusercontent.com/victorfigueira/audit-kit/main/get.sh | bash
# Only one tool:
#   curl -fsSL https://raw.githubusercontent.com/victorfigueira/audit-kit/main/get.sh | bash -s -- antigravity
# Options (environment variables):
#   AUDIT_KIT_REPO  repository to download from (default below)
#   AUDIT_KIT_REF   branch or tag, for example v1.0.0 (default: main)
set -euo pipefail

REPO="${AUDIT_KIT_REPO:-https://github.com/victorfigueira/audit-kit.git}"
REF="${AUDIT_KIT_REF:-main}"
TARGET="${1:-all}"

command -v git >/dev/null || { echo "git is required."; exit 1; }

# Install at the root of the current git project, or the current folder if it is not a git project.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
echo "Project: $ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading audit-kit ($REF) from $REPO"
git clone --quiet --depth 1 --branch "$REF" "$REPO" "$TMP/audit-kit"
rm -rf "$TMP/audit-kit/.git"

if [ -d audit-kit ]; then
  echo "Replacing existing audit-kit folder (your audit/ folder and project context are not touched)."
  rm -rf audit-kit
fi
mv "$TMP/audit-kit" audit-kit

bash audit-kit/install.sh "$TARGET"
