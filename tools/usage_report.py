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
import subprocess
import sys

TYPES = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
TAG = re.compile(r"audit-kit-agent:\s*([a-z0-9-]+)", re.I)

# ---------------------------------------------------------------------------
# Pricing Matrix (USD per 1,000,000 tokens)
# ---------------------------------------------------------------------------
MODEL_PRICING = {
    # Anthropic Claude
    "claude-opus": {"input": 15.00, "output": 75.00, "cache_write": 18.75, "cache_read": 1.50, "label": "Claude 3 / 3.5 Opus"},
    "claude-sonnet": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30, "label": "Claude 3.5 / 3.7 Sonnet"},
    "claude-haiku": {"input": 0.80, "output": 4.00, "cache_write": 1.00, "cache_read": 0.08, "label": "Claude 3.5 Haiku"},
    
    # Google Gemini
    "gemini-pro": {"input": 1.25, "output": 5.00, "cache_write": 1.25, "cache_read": 0.3125, "label": "Gemini 1.5 / 2.5 Pro"},
    "gemini-flash": {"input": 0.10, "output": 0.40, "cache_write": 0.10, "cache_read": 0.025, "label": "Gemini 1.5 / 2.0 Flash"},
    
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00, "cache_write": 2.50, "cache_read": 1.25, "label": "GPT-4o"},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "cache_write": 0.15, "cache_read": 0.075, "label": "GPT-4o mini"},
    "o1": {"input": 15.00, "output": 60.00, "cache_write": 15.00, "cache_read": 7.50, "label": "OpenAI o1"},
    "o3-mini": {"input": 1.10, "output": 4.40, "cache_write": 1.10, "cache_read": 0.55, "label": "OpenAI o3-mini"},

    # Standard model fallback (Sonnet-tier baseline)
    "default": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30, "label": "Standard AI Model (3.00 / 15.00 USD per 1M)"}
}


def match_model_pricing(model_name):
    if not model_name:
        return MODEL_PRICING["default"]
    m = str(model_name).lower()
    if "opus" in m:
        return MODEL_PRICING["claude-opus"]
    if "sonnet" in m:
        return MODEL_PRICING["claude-sonnet"]
    if "haiku" in m:
        return MODEL_PRICING["claude-haiku"]
    if "gemini" in m:
        if "flash" in m:
            return MODEL_PRICING["gemini-flash"]
        return MODEL_PRICING["gemini-pro"]
    if "gpt-4o-mini" in m:
        return MODEL_PRICING["gpt-4o-mini"]
    if "gpt-4o" in m:
        return MODEL_PRICING["gpt-4o"]
    if "o1" in m:
        return MODEL_PRICING["o1"]
    if "o3-mini" in m:
        return MODEL_PRICING["o3-mini"]
    return MODEL_PRICING["default"]


def compute_cost(totals, models):
    model_name = models[0] if (models and isinstance(models, list) and len(models) > 0) else "default"
    pricing = match_model_pricing(model_name)
    
    in_tok = totals.get("input_tokens", 0)
    out_tok = totals.get("output_tokens", 0)
    cw_tok = totals.get("cache_creation_input_tokens", 0)
    cr_tok = totals.get("cache_read_input_tokens", 0)

    in_cost = (in_tok / 1_000_000.0) * pricing["input"]
    out_cost = (out_tok / 1_000_000.0) * pricing["output"]
    cw_cost = (cw_tok / 1_000_000.0) * pricing["cache_write"]
    cr_cost = (cr_tok / 1_000_000.0) * pricing["cache_read"]
    total = in_cost + out_cost + cw_cost + cr_cost

    formatted = f"${total:.2f}" if total >= 0.01 else (f"${total:.3f}" if total > 0 else "$0.00")

    return {
        "total_usd": round(total, 4),
        "currency": "USD",
        "formatted": formatted,
        "breakdown": {
            "input_usd": round(in_cost, 4),
            "output_usd": round(out_cost, 4),
            "cache_write_usd": round(cw_cost, 4),
            "cache_read_usd": round(cr_cost, 4)
        },
        "pricing_applied": pricing["label"],
        "rates_per_million": {
            "input": pricing["input"],
            "output": pricing["output"],
            "cache_write": pricing["cache_write"],
            "cache_read": pricing["cache_read"]
        }
    }

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
    tot_dict = {**totals, "total_tokens": sum(totals.values())}
    sorted_models = sorted(all_models, key=lambda k: -all_models[k])
    return {
        "available": True,
        "source": "Claude Code session files",
        "since": since_str,
        "totals": tot_dict,
        "models": sorted_models,
        "cost": compute_cost(tot_dict, sorted_models),
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

    tot_dict = {**totals, "total_tokens": sum(totals.values())}
    sorted_models = sorted(list(models))
    return {
        "available": True,
        "source": "Antigravity session transcripts",
        "since": since_str,
        "totals": tot_dict,
        "models": sorted_models,
        "cost": compute_cost(tot_dict, sorted_models),
        "agents": agents,
        "notes": "Counted from local Antigravity transcript logs. Subagent tokens attributed via invoke_subagent conversation logs.",
    }


# ---------------------------------------------------------------------------
# Deterministic token estimation fallback
# ---------------------------------------------------------------------------

DIMENSIONS = [
    "maintainability", "oss-health", "architecture", "security", "reliability",
    "performance-scalability", "testing-qa", "observability-operability",
    "data-privacy", "infra-cicd-cost"
]


def estimate_usage(root, since_str, since=None):
    """Deterministic token estimate based on repository size and generated audit reports."""
    size_script = os.path.join(os.path.dirname(__file__), "size_check.py")
    code_tokens = 50_000
    if os.path.isfile(size_script):
        try:
            out = subprocess.check_output(
                [sys.executable, size_script, "--json"],
                cwd=root,
                stderr=subprocess.DEVNULL
            )
            data = json.loads(out)
            code_tokens = int(data.get("estimated_tokens") or 50_000)
        except Exception:
            pass

    audit_dir = os.path.join(root, "audit")
    agents = []
    total_out_chars = 0

    if os.path.isdir(audit_dir):
        # 1. Individual auditor reports
        for dim in DIMENSIONS:
            rep_path = os.path.join(audit_dir, f"{dim}.md")
            if os.path.isfile(rep_path):
                mtime = os.path.getmtime(rep_path)
                if since and dt.datetime.fromtimestamp(mtime, dt.timezone.utc) < since:
                    continue
                size_chars = os.path.getsize(rep_path)
                total_out_chars += size_chars
                out_tok = max(1, size_chars // 4)
                # Input overhead: prompt (~1200) + code in scope
                in_tok = 1200 + code_tokens
                agents.append({
                    "agent": dim,
                    "runs": 1,
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0
                })

        # 2. Skeptic verifier
        verif_path = os.path.join(audit_dir, "verification.md")
        if os.path.isfile(verif_path):
            size_chars = os.path.getsize(verif_path)
            total_out_chars += size_chars
            out_tok = max(1, size_chars // 4)
            in_tok = max(3000, out_tok * 4)
            agents.append({
                "agent": "skeptic-verifier",
                "runs": 1,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0
            })

        # 3. Triage
        triage_path = os.path.join(audit_dir, "triage.md")
        if os.path.isfile(triage_path):
            size_chars = os.path.getsize(triage_path)
            total_out_chars += size_chars
            out_tok = max(1, size_chars // 4)
            in_tok = 2500 + min(15000, code_tokens // 4)
            agents.append({
                "agent": "triage",
                "runs": 1,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0
            })

        # 4. Manager
        audit_md = os.path.join(audit_dir, "AUDIT.md")
        audit_chars = os.path.getsize(audit_md) if os.path.isfile(audit_md) else 2000
        mgr_out_tok = max(1, audit_chars // 4)
        mgr_in_tok = 2000 + (total_out_chars // 4)
        agents.insert(0, {
            "agent": "manager",
            "runs": 1,
            "input_tokens": mgr_in_tok,
            "output_tokens": mgr_out_tok,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0
        })

    # If no audit files found yet, provide baseline manager run
    if not agents:
        agents.append({
            "agent": "manager",
            "runs": 1,
            "input_tokens": 2000 + code_tokens,
            "output_tokens": 1000,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0
        })

    totals = {
        "input_tokens": sum(a["input_tokens"] for a in agents),
        "output_tokens": sum(a["output_tokens"] for a in agents),
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0
    }
    totals["total_tokens"] = totals["input_tokens"] + totals["output_tokens"]

    models = ["Estimated (Model-neutral)"]
    return {
        "available": True,
        "estimated": True,
        "source": "Deterministic estimate (code size and report lengths)",
        "since": since_str,
        "totals": totals,
        "models": models,
        "cost": compute_cost(totals, models),
        "agents": agents,
        "notes": "Calculated deterministically at 4 chars/token over repository code size and generated audit reports. Used as fallback when native session logs are absent.",
    }


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Sum audit tokens from local AI session transcripts.")
    ap.add_argument("--since", help="audit start time, ISO 8601 (UTC)")
    ap.add_argument("--root", default=".", help="project root directory (default: .)")
    ap.add_argument("--engine", choices=["auto", "claude", "antigravity", "estimate"], default="auto",
                    help="AI session engine (default: auto)")
    ap.add_argument("--conversation-id", help="Antigravity conversation ID if known")
    ap.add_argument("--estimate", action="store_true", help="Force deterministic estimation fallback")
    ap.add_argument("--no-fallback", action="store_true", help="Disable estimation fallback when sessions are missing")
    args = ap.parse_args()

    since = parse_ts(args.since) if args.since else None

    # Forced estimation
    if args.estimate or args.engine == "estimate":
        res = estimate_usage(args.root, args.since, since)
        print(json.dumps(res, indent=2))
        return

    # Antigravity engine requested
    if args.engine == "antigravity":
        t_path, brain_dir = find_antigravity_transcript(args.root, since, args.conversation_id)
        if t_path:
            res = process_antigravity(t_path, brain_dir, since, args.since)
            if res:
                print(json.dumps(res, indent=2))
                return
        if not args.no_fallback:
            res = estimate_usage(args.root, args.since, since)
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
        if not args.no_fallback:
            res = estimate_usage(args.root, args.since, since)
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

    # 4. Fallback to estimation unless explicitly disabled
    if not args.no_fallback:
        res = estimate_usage(args.root, args.since, since)
        print(json.dumps(res, indent=2))
        return

    print(json.dumps({
        "available": False,
        "reason": "No Claude Code or Antigravity session files found for this project."
    }, indent=2))


if __name__ == "__main__":
    main()
