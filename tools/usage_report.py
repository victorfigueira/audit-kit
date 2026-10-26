#!/usr/bin/env python3
"""Sum the tokens an audit consumed, from Claude Code or Antigravity local session files.

Usage (from the project root, at the end of an audit):
  python3 audit-kit/tools/usage_report.py --since 2026-10-23T10:00:00Z

Supports:
- Claude Code: reads ~/.claude/projects/<encoded project path>/
- Antigravity: reads ~/.gemini/antigravity/brain/<conversation-id>/.system_generated/logs/transcript.jsonl
  and any invoked subagent transcript files.

Counts only records at or after --since. Reads numbers and agent tags only,
never copies user code. Prints JSON; "available": false when session files are absent.
"""
import argparse
import datetime as dt
import glob
import json
import os
import re

TYPES = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
TAG = re.compile(r"audit-kit-agent:\s*([a-z0-9-]+)", re.I)
# Fallback only, for subagents started without the tag. Order matters.
AGENT_HINTS = [
    ("skeptic-verifier", r"skeptic[\s_-]*verifier|verification"),
    ("audit-triage", r"\btriage\b"),
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
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Claude Code session parsing
# ---------------------------------------------------------------------------

def claude_project_dir(root):
    base = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude"))
    encoded = re.sub(r"[^A-Za-z0-9-]", "-", os.path.abspath(root))
    path = os.path.join(base, "projects", encoded)
    return path if os.path.isdir(path) else None


def first_user_text_claude(records):
    for r in records:
        if r.get("type") == "user":
            c = r.get("message", {}).get("content")
            if isinstance(c, str):
                return c
            if isinstance(c, list):
                return " ".join(b.get("text", "") for b in c if isinstance(b, dict))
    return ""


def agent_name_from_text(text, fallback):
    if not text:
        return fallback
    tag = TAG.search(text[:500])
    if tag:
        name = tag.group(1).lower()
        return name[:-len("-auditor")] if name.endswith("-auditor") else name
    text_sub = text[:300].lower()
    for name, pattern in AGENT_HINTS:
        if re.search(pattern, text_sub):
            return name
    return fallback


def read_jsonl(path):
    out = []
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def tally_claude_records(records, since, seen):
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
        if key in seen:
            continue
        seen.add(key)
        for t in TYPES:
            total[t] += int(usage.get(t) or 0)
        if msg.get("model"):
            models[msg["model"]] = models.get(msg["model"], 0) + 1
    return total, models


def process_claude(pdir, since, since_str):
    sessions = sorted(glob.glob(os.path.join(pdir, "*.jsonl")), key=os.path.getmtime)
    if not sessions:
        return None
    main_file = sessions[-1]
    sid = os.path.splitext(os.path.basename(main_file))[0]
    sub_files = sorted(set(glob.glob(os.path.join(pdir, sid, "subagents", "*.jsonl"))
                           + glob.glob(os.path.join(pdir, sid, "agent-*.jsonl"))))

    seen = set()
    agents = []
    main_records = read_jsonl(main_file)
    manager = [r for r in main_records if not r.get("isSidechain")]
    sidechain = [r for r in main_records if r.get("isSidechain")]
    tot, models = tally_claude_records(manager, since, seen)
    agents.append({"agent": "manager", **tot})
    all_models = dict(models)
    groups = [(f, read_jsonl(f)) for f in sub_files]
    if sidechain:
        groups.append(("sidechain", sidechain))
    for i, (src, recs) in enumerate(groups, 1):
        t, m = tally_claude_records(recs, since, seen)
        if sum(t.values()) == 0:
            continue
        agent_name = agent_name_from_text(first_user_text_claude(recs), f"subagent-{i}")
        agents.append({"agent": agent_name, **t})
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
    return {
        "available": True,
        "source": "Claude Code session files",
        "since": since_str,
        "totals": {**totals, "total_tokens": sum(totals.values())},
        "models": sorted(all_models, key=lambda k: -all_models[k]),
        "agents": agents,
        "notes": "Counted from local Claude Code logs. Agent names matched from subagent prompts.",
    }


# ---------------------------------------------------------------------------
# Antigravity session parsing
# ---------------------------------------------------------------------------

def antigravity_brain_dir():
    candidates = [
        os.environ.get("ANTIGRAVITY_APP_DATA_DIR"),
        os.environ.get("GEMINI_DATA_DIR"),
        os.path.expanduser("~/.gemini/antigravity"),
        os.path.expanduser("~/Library/Application Support/Antigravity"),
    ]
    for c in candidates:
        if c:
            b = os.path.join(c, "brain")
            if os.path.isdir(b):
                return b
    return None


def find_antigravity_transcript(root, since=None, conv_id=None):
    brain_dir = antigravity_brain_dir()
    if not brain_dir:
        return None, None

    # 1. Direct conversation ID from env or arg
    target_id = conv_id or os.environ.get("ANTIGRAVITY_CONVERSATION_ID")
    if target_id:
        t_path = os.path.join(brain_dir, target_id, ".system_generated", "logs", "transcript.jsonl")
        if os.path.isfile(t_path):
            return t_path, brain_dir

    # 2. Match conversation directory touching this workspace
    root_abs = os.path.abspath(root)
    candidates = []
    try:
        conv_dirs = sorted(glob.glob(os.path.join(brain_dir, "*")), key=os.path.getmtime, reverse=True)
    except OSError:
        conv_dirs = []

    for d in conv_dirs:
        if not os.path.isdir(d):
            continue
        t_path = os.path.join(d, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.isfile(t_path):
            continue
        try:
            mtime = os.path.getmtime(t_path)
            if since and dt.datetime.fromtimestamp(mtime, dt.timezone.utc) < since:
                continue
            with open(t_path, encoding="utf-8", errors="replace") as f:
                head = "".join(f.readline() for _ in range(8))
                if root_abs in head:
                    return t_path, brain_dir
            candidates.append((mtime, t_path))
        except OSError:
            continue

    if candidates:
        return candidates[0][1], brain_dir
    return None, brain_dir


def extract_subagent_cids(records):
    """Find any subagents invoked in this session: returns list of (agent_name, conversation_id)."""
    subagents = []
    pending_prompt = None

    for r in records:
        tool_calls = r.get("tool_calls") or []
        for tc in tool_calls:
            if tc.get("name") == "invoke_subagent":
                args = tc.get("args") or {}
                prompt = args.get("Prompt") or ""
                role = args.get("Role") or "subagent"
                agent_name = agent_name_from_text(prompt, role)
                pending_prompt = agent_name

        content = r.get("content") or ""
        if isinstance(content, str) and pending_prompt:
            # Check for conversationId in response or message
            cid_match = re.search(r'["\']?conversationId["\']?\s*:\s*["\']([a-f0-9-]{36})["\']', content, re.I)
            if not cid_match:
                cid_match = re.search(r'([a-f0-9-]{36})', content)
            if cid_match:
                subagents.append((pending_prompt, cid_match.group(1)))
                pending_prompt = None

    return subagents


def tally_antigravity_file(transcript_path, since):
    counts = {t: 0 for t in TYPES}
    models = set()
    records = read_jsonl(transcript_path)
    step_count = 0

    for r in records:
        ts = parse_ts(r.get("created_at"))
        if since and ts and ts < since:
            continue

        c = r.get("content", "")
        if isinstance(c, str):
            m = re.search(r"Model Selection\`\s+from\s+.*?\s+to\s+([A-Za-z0-9. ()-]+?)(?:\.\s+[A-Z]|\n|$)", c)
            if m:
                model_clean = m.group(1).strip()
                if model_clean:
                    models.add(model_clean)

        if "input_tokens" in r or "output_tokens" in r:
            step_count += 1
            counts["input_tokens"] += int(r.get("input_tokens") or 0)
            counts["output_tokens"] += int(r.get("output_tokens") or 0)
            counts["cache_read_input_tokens"] += int(r.get("cache_read_tokens") or 0)
            counts["cache_creation_input_tokens"] += int(r.get("cache_creation_input_tokens") or 0)

    return counts, models, records, step_count


def process_antigravity(transcript_path, brain_dir, since, since_str):
    manager_counts, models, records, manager_steps = tally_antigravity_file(transcript_path, since)
    if manager_steps == 0 and sum(manager_counts.values()) == 0:
        return None

    agents = [{"agent": "manager", "runs": 1, **manager_counts}]

    # Check for subagents in child transcripts
    subagents = extract_subagent_cids(records)
    for agent_name, cid in subagents:
        sub_path = os.path.join(brain_dir, cid, ".system_generated", "logs", "transcript.jsonl")
        if os.path.isfile(sub_path):
            sub_counts, sub_models, _, sub_steps = tally_antigravity_file(sub_path, since)
            if sum(sub_counts.values()) > 0:
                agents.append({"agent": agent_name, "runs": 1, **sub_counts})
                models.update(sub_models)

    # Consolidate duplicate agent rows if any
    merged = {}
    for a in agents:
        m = merged.setdefault(a["agent"], {"agent": a["agent"], "runs": 0, **{t: 0 for t in TYPES}})
        m["runs"] += a["runs"]
        for t in TYPES:
            m[t] += a[t]
    agents = list(merged.values())

    totals = {t: sum(a[t] for a in agents) for t in TYPES}
    if not models:
        models.add("Gemini (Antigravity)")

    return {
        "available": True,
        "source": "Antigravity session transcripts",
        "since": since_str,
        "totals": {**totals, "total_tokens": sum(totals.values())},
        "models": sorted(list(models)),
        "agents": agents,
        "notes": "Counted from local Antigravity transcript logs. Subagent tokens attributed via invoke_subagent conversation logs.",
    }


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Sum audit tokens from local AI session transcripts.")
    ap.add_argument("--since", help="audit start time, ISO 8601 (UTC)")
    ap.add_argument("--root", default=".", help="project root directory (default: .)")
    ap.add_argument("--engine", choices=["auto", "claude", "antigravity"], default="auto",
                    help="AI session engine (default: auto)")
    ap.add_argument("--conversation-id", help="Antigravity conversation ID if known")
    args = ap.parse_args()

    since = parse_ts(args.since) if args.since else None

    # Antigravity engine requested
    if args.engine == "antigravity":
        t_path, brain_dir = find_antigravity_transcript(args.root, since, args.conversation_id)
        if t_path:
            res = process_antigravity(t_path, brain_dir, since, args.since)
            if res:
                print(json.dumps(res, indent=2))
                return
        print(json.dumps({
            "available": False,
            "reason": "No Antigravity transcript logs found for this project or time range."
        }, indent=2))
        return

    # Claude Code engine requested
    if args.engine == "claude":
        pdir = claude_project_dir(args.root)
        if pdir:
            res = process_claude(pdir, since, args.since)
            if res:
                print(json.dumps(res, indent=2))
                return
        print(json.dumps({
            "available": False,
            "reason": "No Claude Code session files for this project."
        }, indent=2))
        return

    # Auto engine detection
    # 1. If running under Antigravity environment, prioritize Antigravity
    if os.environ.get("ANTIGRAVITY_AGENT") or os.environ.get("ANTIGRAVITY_CONVERSATION_ID"):
        t_path, brain_dir = find_antigravity_transcript(args.root, since, args.conversation_id)
        if t_path:
            res = process_antigravity(t_path, brain_dir, since, args.since)
            if res:
                print(json.dumps(res, indent=2))
                return

    # 2. Check Claude Code sessions
    pdir = claude_project_dir(args.root)
    if pdir:
        res = process_claude(pdir, since, args.since)
        if res:
            print(json.dumps(res, indent=2))
            return

    # 3. Check Antigravity files if not detected by env var
    t_path, brain_dir = find_antigravity_transcript(args.root, since, args.conversation_id)
    if t_path:
        res = process_antigravity(t_path, brain_dir, since, args.since)
        if res:
            print(json.dumps(res, indent=2))
            return

    print(json.dumps({
        "available": False,
        "reason": "No Claude Code or Antigravity session files found for this project."
    }, indent=2))


if __name__ == "__main__":
    main()
