#!/usr/bin/env bash
# Install audit-kit adapters into the project that contains this folder.
# Usage (from the project root):  bash audit-kit/install.sh [claude|antigravity|gemini|all]
set -euo pipefail

TARGET="all"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target=*) TARGET="${1#*=}"; shift ;;
    --target) TARGET="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash audit-kit/install.sh [options] [target]"
      echo ""
      echo "Targets:  all, claude, antigravity, gemini, auto"
      echo "Options:"
      echo "  --target <target>   Specify installation target"
      echo "  -h, --help          Show this help message"
      exit 0 ;;
    claude|antigravity|gemini|all|auto) TARGET="$1"; shift ;;
    *) echo "Unknown option or target: $1 (use claude, antigravity, gemini, all, or auto)"; exit 1 ;;
  esac
done

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$KIT")"
cd "$ROOT"

# Auto-detect target if requested
if [ "$TARGET" = "auto" ]; then
  DETECTED=()
  [ -d .claude ] && DETECTED+=(claude)
  ([ -d .agents ] || [ -d .agent ] || [ -f GEMINI.md ]) && DETECTED+=(antigravity)
  [ -d .gemini ] && DETECTED+=(gemini)
  if [ ${#DETECTED[@]} -eq 0 ]; then
    TARGET="all"
  elif [ ${#DETECTED[@]} -eq 1 ]; then
    TARGET="${DETECTED[0]}"
    echo "Auto-detected platform target: $TARGET"
  else
    TARGET="all"
    echo "Detected multiple platforms (${DETECTED[*]}); installing all"
  fi
fi

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
  echo "Unknown target: $TARGET (use claude, antigravity, gemini, all, or auto)"; exit 1 ;; esac

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
  # Auto-migrate legacy .agent folder if present without .agents
  if [ -d .agent ] && [ ! -d .agents ]; then
    echo "  migrating legacy .agent/ -> .agents/"
    mv .agent .agents
  fi
  if [ -d "$KIT/adapters/antigravity/skills" ]; then
    copy_skills "$KIT/adapters/antigravity/skills" .agents/skills
  fi
  copy_dir "$KIT/adapters/antigravity/workflows" .agents/workflows
  if [ -d "$KIT/adapters/antigravity/rules" ]; then
    copy_dir "$KIT/adapters/antigravity/rules" .agents/rules
  fi
  if [ -f GEMINI.md ]; then
    add_rules GEMINI.md
  fi
fi
if [ "$TARGET" = gemini ] || [ "$TARGET" = all ]; then
  echo "Gemini CLI:"
  copy_dir "$KIT/adapters/gemini/commands" .gemini/commands
fi

echo "Done. Reload your IDE window so the new commands appear."
