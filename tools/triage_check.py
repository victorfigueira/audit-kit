#!/usr/bin/env python3
"""Deterministic checks that decide whether an incremental audit must rerun auditors.

Usage (from the project root):
  python3 audit-kit/tools/triage_check.py --mode standard|full --tool "<tool>" --model "<model>"

Prints JSON. The manager and the triage agent must follow it: these checks are
arithmetic and are never left to judgement.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess

STANDARD = ["Maintainability", "Open Source Health", "Architecture", "Security", "Reliability"]
FULL = STANDARD + ["Performance and Scalability", "Testing and QA", "Observability and Operability",
                   "Data and Privacy Compliance", "Infra, CI/CD and Cloud Cost"]
AGEING = {"Security": 30, "Open Source Health": 30}
VERIFIED = ("Confirmed", "Downgraded", "Inconclusive", "Reinstated by user")


def sha256(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def major(version):
    try:
        return int(str(version).split(".")[0])
    except (ValueError, IndexError):
        return None


def commit_exists(commit):
    if not commit:
        return False
    r = subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], capture_output=True)
    return r.returncode == 0


KIT_PATHS = ("audit/", "audit-kit/")


def untracked_hashes():
    r = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z"], capture_output=True)
    out = {}
    for path in r.stdout.decode("utf-8", "replace").split("\0"):
        if path and not path.startswith(KIT_PATHS) and os.path.isfile(path):
            out[path] = sha256(path)
    return out


def known(value):
    return value not in (None, "", "unknown")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["standard", "full"], required=True)
    ap.add_argument("--tool", default="unknown")
    ap.add_argument("--model", default="unknown")
    ap.add_argument("--fresh", action="store_true", help="the user asked for a fresh audit")
    ap.add_argument("--findings", default="audit/findings.json")
    ap.add_argument("--context", default="audit/project-context.md")
    ap.add_argument("--version-file", default="audit-kit/VERSION")
    args = ap.parse_args()

    dims = STANDARD if args.mode == "standard" else FULL
    kit_version = open(args.version_file).read().strip() if os.path.exists(args.version_file) else "unknown"
    context_hash = sha256(args.context)
    out = {"kit_version": kit_version, "context_hash": context_hash,
           "fresh_required": False, "reasons": [], "notes": [],
           "force_dimensions": {}, "unverified_findings": [], "previous_commit": None,
           "untracked_hashes": untracked_hashes(), "untracked_changed": []}
    out["untracked_changed"] = sorted(out["untracked_hashes"])

    if args.fresh:
        out["reasons"].append("The user asked for a fresh audit.")
    if not os.path.exists(args.findings):
        out["reasons"].append("No previous audit.")
    else:
        with open(args.findings, encoding="utf-8") as fh:
            prev = json.load(fh)
        out["previous_commit"] = prev.get("commit")
        pv = prev.get("kit_version")
        if not pv:
            out["reasons"].append("The previous audit has no kit version.")
        elif major(pv) != major(kit_version):
            out["reasons"].append(f"Kit major version changed ({pv} -> {kit_version}).")
        if not commit_exists(prev.get("commit")):
            out["reasons"].append(f"Previous commit {prev.get('commit')} no longer exists.")
        ph = prev.get("context_hash")
        if not ph:
            out["notes"].append("Previous audit has no context hash; project context check skipped.")
        elif ph != context_hash:
            out["reasons"].append("audit/project-context.md changed.")
        for field, current in (("tool", args.tool), ("model", args.model)):
            before = prev.get(field)
            if known(before) and known(current):
                if before != current:
                    out["reasons"].append(f"The {field} changed ({before} -> {current}).")
            else:
                out["notes"].append(f"{field.capitalize()} unknown on one side; {field} check skipped.")

        before = prev.get("untracked_hashes")
        if isinstance(before, dict):
            out["untracked_changed"] = sorted(p for p, h in out["untracked_hashes"].items() if before.get(p) != h)
        else:
            out["notes"].append("Previous audit has no untracked file hashes; every untracked file counts as changed.")

        entries = prev.get("dimensions", {})
        today = dt.date.today()
        for d in dims:
            e = entries.get(d)
            if not e or e.get("score") in (None, "Not completed"):
                out["force_dimensions"][d] = "Never audited or not completed."
                continue
            if d in AGEING:
                try:
                    age = (today - dt.date.fromisoformat(str(e.get("date")))).days
                    if age > AGEING[d]:
                        out["force_dimensions"][d] = f"Last real check {age} days ago (limit {AGEING[d]})."
                except ValueError:
                    out["force_dimensions"][d] = "Date of last real check unreadable."
        for f in prev.get("findings", []):
            if f.get("severity") in ("Critical", "High") and f.get("dimension") in dims \
                    and f.get("verification") not in VERIFIED:
                out["unverified_findings"].append(f.get("id"))

    out["fresh_required"] = bool(out["reasons"])
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
