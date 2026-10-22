#!/usr/bin/env python3
"""Sum the tokens an audit consumed, from Claude Code's local session files.

Usage (from the project root, at the end of an audit):
  python3 audit-kit/tools/usage_report.py --since 2026-10-23T10:00:00Z

Reads ~/.claude/projects/<encoded project path>/: the latest session file and its
subagent files. Counts only records at or after --since. Reads numbers only and
never copies prompts or code. Prints JSON; "available": false when the files are
not there (for example in Antigravity or Gemini CLI).
"""
import argparse
import datetime as dt
import glob
import json
import os
import re

TYPES = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
AGENT_HINTS = [
    ("skeptic-verifier", r"skeptic verifier"),
    ("audit-triage", r"triage agent"),
    ("maintainability", r"maintainability"),
    ("oss-health", r"open source health|oss-health"),
    ("architecture", r"architecture"),
    ("security", r"security"),
    ("reliability", r"reliability"),
    ("performance-scalability", r"performance"),
    ("testing-qa", r"testing"),
    ("observability-operability", r"observability"),
    ("data-privacy", r"privacy"),
    ("infra-cicd-cost", r"infra|ci/cd"),
]


def parse_ts(value):
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def project_dir(root):
    base = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude"))
    encoded = re.sub(r"[^A-Za-z0-9-]", "-", os.path.abspath(root))
    path = os.path.join(base, "projects", encoded)
    return path if os.path.isdir(path) else None


def first_user_text(records):
    for r in records:
        if r.get("type") == "user":
            c = r.get("message", {}).get("content")
            if isinstance(c, str):
                return c
            if isinstance(c, list):
                return " ".join(b.get("text", "") for b in c if isinstance(b, dict))
    return ""


def agent_name(records, fallback):
    text = first_user_text(records)[:2000].lower()
    for name, pattern in AGENT_HINTS:
        if re.search(pattern, text):
            return name
    return fallback


def read(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def tally(records, since, seen):
    total = {t: 0 for t in TYPES}
    models = {}
    for r in records:
        msg = r.get("message") or {}
        usage = msg.get("usage")
        if r.get("type") != "assistant" or not usage:
            continue
        ts = parse_ts(r.get("timestamp"))
        if since and (ts is None or ts < since):
            continue
        key = msg.get("id") or r.get("requestId") or r.get("uuid")
        if key in seen:  # one API response can be written as several records
            continue
        seen.add(key)
        for t in TYPES:
            total[t] += int(usage.get(t) or 0)
        if msg.get("model"):
            models[msg["model"]] = models.get(msg["model"], 0) + 1
    return total, models


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="audit start time, ISO 8601 (UTC)")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    since = parse_ts(args.since) if args.since else None

    pdir = project_dir(args.root)
    sessions = sorted(glob.glob(os.path.join(pdir, "*.jsonl")), key=os.path.getmtime) if pdir else []
    if not sessions:
        print(json.dumps({"available": False,
                          "reason": "No Claude Code session files for this project."}, indent=2))
        return
    main_file = sessions[-1]
    sid = os.path.splitext(os.path.basename(main_file))[0]
    sub_files = sorted(set(glob.glob(os.path.join(pdir, sid, "subagents", "*.jsonl"))
                           + glob.glob(os.path.join(pdir, sid, "agent-*.jsonl"))))

    seen = set()
    agents = []
    main_records = read(main_file)
    manager = [r for r in main_records if not r.get("isSidechain")]
    sidechain = [r for r in main_records if r.get("isSidechain")]
    tot, models = tally(manager, since, seen)
    agents.append({"agent": "manager", **tot})
    all_models = dict(models)
    groups = [(f, read(f)) for f in sub_files]
    if sidechain:
        groups.append(("sidechain", sidechain))
    for i, (src, recs) in enumerate(groups, 1):
        t, m = tally(recs, since, seen)
        if sum(t.values()) == 0:
            continue
        agents.append({"agent": agent_name(recs, f"subagent-{i}"), **t})
        for k, v in m.items():
            all_models[k] = all_models.get(k, 0) + v

    merged = {}
    for a in agents:
        m = merged.setdefault(a["agent"], {"agent": a["agent"], "runs": 0, **{t: 0 for t in TYPES}})
        m["runs"] += 1
        for t in TYPES:
            m[t] += a[t]
    agents = list(merged.values())
    totals = {t: sum(a[t] for a in agents) for t in TYPES}
    result = {
        "available": True,
        "source": "Claude Code session files",
        "since": args.since,
        "totals": {**totals, "total_tokens": sum(totals.values())},
        "models": sorted(all_models, key=lambda k: -all_models[k]),
        "agents": agents,
        "notes": "Counted from local logs, an undocumented format that may change. Agent names are matched from each subagent's first prompt (best effort). The manager's last messages after this report are not included.",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
