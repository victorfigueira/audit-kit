#!/usr/bin/env bash
# Install audit-kit adapters into the project that contains this folder.
# Usage (from the project root):  bash audit-kit/install.sh [claude|antigravity|gemini|all]
set -euo pipefail

TARGET="${1:-all}"
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$KIT")"
cd "$ROOT"

copy_dir() { # src dst
  # Adapters that point to audit-kit/ are the kit's own and are refreshed.
  # Any other file with the same name is left alone.
  mkdir -p "$2"
  for f in "$1"/*; do
    local dest="$2/$(basename "$f")"
    if [ ! -e "$dest" ]; then
      cp "$f" "$dest"; echo "  added: $dest"
    elif cmp -s "$f" "$dest"; then
      echo "  up to date: $dest"
    elif grep -q "audit-kit/" "$dest"; then
      cp "$f" "$dest"; echo "  updated: $dest"
    else
      echo "  skip (not an audit-kit file): $dest"
    fi
  done
}

copy_skills() { # src dst
  mkdir -p "$2"
  for s in "$1"/*; do
    [ -d "$s" ] || continue
    local sname="$(basename "$s")"
    mkdir -p "$2/$sname"
    for f in "$s"/*; do
      [ -f "$f" ] || continue
      local dest="$2/$sname/$(basename "$f")"
      if [ ! -e "$dest" ]; then
        cp "$f" "$dest"; echo "  added: $dest"
      elif cmp -s "$f" "$dest"; then
        echo "  up to date: $dest"
      elif grep -q "audit-kit" "$dest" 2>/dev/null; then
        cp "$f" "$dest"; echo "  updated: $dest"
      else
        echo "  skip (not an audit-kit file): $dest"
      fi
    done
  done
}

add_rules() { # file
  if [ -f "$1" ] && grep -q "audit-kit:start" "$1"; then
    echo "  skip (already has audit rules): $1"
  else
    cat "$KIT/adapters/rules-snippet.md" >> "$1"; echo "  updated: $1"
  fi
}

case "$TARGET" in claude|antigravity|gemini|all) ;; *)
  echo "Unknown target: $TARGET (use claude, antigravity, gemini or all)"; exit 1 ;; esac

echo "Installing audit-kit $(cat "$KIT/VERSION" 2>/dev/null) into $ROOT"

# Excel tracker dependency (optional: the audit runs without it)
if command -v python3 >/dev/null; then
  if python3 -c "import openpyxl" 2>/dev/null; then
    echo "  openpyxl: already installed"
  elif python3 -m pip install --user --quiet openpyxl 2>/dev/null \
    || python3 -m pip install --user --quiet --break-system-packages openpyxl 2>/dev/null; then
    echo "  openpyxl: installed"
  else
    echo "  openpyxl: could not install; run 'python3 -m pip install --user openpyxl' for the Excel tracker"
  fi
else
  echo "  python3 not found: the Excel tracker will be skipped"
fi
mkdir -p audit
if [ ! -f audit/project-context.md ]; then
  cp "$KIT/templates/project-context.md" audit/project-context.md
  echo "  added: audit/project-context.md (fill it in)"
fi
add_rules AGENTS.md

if [ "$TARGET" = claude ] || [ "$TARGET" = all ]; then
  echo "Claude Code:"
  copy_dir "$KIT/adapters/claude/agents" .claude/agents
  copy_dir "$KIT/adapters/claude/commands" .claude/commands
  add_rules CLAUDE.md
fi
if [ "$TARGET" = antigravity ] || [ "$TARGET" = all ]; then
  echo "Antigravity:"
  if [ -d "$KIT/adapters/antigravity/skills" ]; then
    copy_skills "$KIT/adapters/antigravity/skills" .agents/skills
  fi
  copy_dir "$KIT/adapters/antigravity/workflows" .agents/workflows
fi
if [ "$TARGET" = gemini ] || [ "$TARGET" = all ]; then
  echo "Gemini CLI:"
  copy_dir "$KIT/adapters/gemini/commands" .gemini/commands
fi

echo "Done. Reload your IDE window so the new commands appear."
