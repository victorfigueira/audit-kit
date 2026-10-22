#!/usr/bin/env python3
"""Measure the code an audit will read and estimate its size in tokens.

Usage (from the project root):
  python3 audit-kit/tools/size_check.py [--json] [--threshold N] [--exclude PATH ...]

Counts text files tracked or not ignored by git, skipping audit/, audit-kit/,
binary files and the out-of-scope paths in audit/project-context.md.
Tokens are estimated at 4 characters per token: a rough, model-neutral figure.
"""
import argparse
import fnmatch
import json
import os
import subprocess
import sys

CHARS_PER_TOKEN = 4
DEFAULT_THRESHOLD = 400_000
ALWAYS_SKIP = ["audit/*", "audit-kit/*", ".claude/agents/*-auditor.md",
               ".claude/agents/audit-triage.md", ".claude/agents/skeptic-verifier.md",
               ".claude/commands/audit*", ".agents/workflows/audit*", ".gemini/commands/audit*"]
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svgz", ".pdf", ".zip",
              ".gz", ".tar", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".mp3", ".mp4",
              ".wav", ".webm", ".mov", ".exe", ".dll", ".so", ".dylib", ".jar", ".bin"}
LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
             "Pipfile.lock", "composer.lock", "Gemfile.lock", "Cargo.lock",
             "packages.lock.json"}


def context_excludes(path="audit/project-context.md"):
    """Read the 'Out of scope paths' entry of the project context.

    Accepts a comma-separated value on the same line or indented bullets below it.
    """
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    items = []
    for i, line in enumerate(lines):
        if not line.strip().lstrip("-*").strip().lower().startswith("out of scope paths"):
            continue
        indent = len(line) - len(line.lstrip())
        value = line.split(":", 1)[1] if ":" in line else ""
        items += value.replace(";", ",").split(",")
        for nxt in lines[i + 1:]:
            if not nxt.strip():
                continue
            nind = len(nxt) - len(nxt.lstrip())
            if nind <= indent:
                break
            items += nxt.strip().lstrip("-*").strip().replace(";", ",").split(",")
        break
    clean = []
    for it in items:
        it = it.strip().strip("`'\"").strip()
        if it and "TO CONFIRM" not in it.upper():
            clean.append(it)
    return clean


def to_patterns(items):
    pats = []
    for i in items:
        i = i.split(" (")[0].split(" - ")[0].strip().strip("`").rstrip("/")
        if not i:
            continue
        pats += [i, f"{i}/*", f"*/{i}/*"] if "*" not in i else [i]
    return pats


def list_files():
    try:
        out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                             capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        sys.exit("Not a git repository, or git is missing. Run from the project root.")
    return [p for p in out.decode("utf-8", "replace").split("\0") if p]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="print JSON only")
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    ap.add_argument("--exclude", nargs="*", default=[])
    args = ap.parse_args()

    patterns = to_patterns(context_excludes() + args.exclude) + ALWAYS_SKIP
    files = lines = chars = lock_chars = skipped = 0
    by_dir = {}
    for path in list_files():
        if any(fnmatch.fnmatch(path, p) for p in patterns) or not os.path.isfile(path):
            continue
        try:
            with open(path, "rb") as fh:
                data = fh.read()
        except OSError:
            continue
        if os.path.splitext(path)[1].lower() in BINARY_EXT or b"\0" in data[:8192]:
            skipped += 1
            continue
        text = data.decode("utf-8", "replace")
        if os.path.basename(path) in LOCKFILES:
            lock_chars += len(text)
            continue
        files += 1
        lines += text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        chars += len(text)
        top = path.split("/")[0] if "/" in path else "(root)"
        by_dir[top] = by_dir.get(top, 0) + len(text)

    tokens = chars // CHARS_PER_TOKEN
    result = {
        "files": files, "lines": lines, "estimated_tokens": tokens,
        "lockfile_estimated_tokens": lock_chars // CHARS_PER_TOKEN,
        "binary_files_skipped": skipped, "excluded_patterns": patterns,
        "largest_folders": [{"folder": d, "estimated_tokens": c // CHARS_PER_TOKEN}
                            for d, c in sorted(by_dir.items(), key=lambda x: -x[1])[:5]],
        "threshold": args.threshold, "over_threshold": tokens > args.threshold,
        "method": f"{CHARS_PER_TOKEN} characters per token (model-neutral estimate)",
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"Code in scope: {files} files, {lines:,} lines, about {tokens:,} tokens")
    print(f"Lockfiles (not counted): about {result['lockfile_estimated_tokens']:,} tokens; binary files skipped: {skipped}")
    for d in result["largest_folders"]:
        print(f"  {d['folder']}: about {d['estimated_tokens']:,} tokens")
    if result["over_threshold"]:
        print(f"Over the threshold of {args.threshold:,} tokens: consider a Standard or Diff audit.")


if __name__ == "__main__":
    main()
