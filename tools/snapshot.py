#!/usr/bin/env python3
"""Manage audit snapshots and compare audit runs.

Usage (from the project root):
  python3 audit-kit/tools/snapshot.py create [--name NAME] [--audit-dir AUDIT_DIR] [--if-exists]
  python3 audit-kit/tools/snapshot.py list [--json] [--audit-dir AUDIT_DIR]
  python3 audit-kit/tools/snapshot.py show <snapshot_id> [--json] [--audit-dir AUDIT_DIR]
  python3 audit-kit/tools/snapshot.py delete <snapshot_id> [--audit-dir AUDIT_DIR]
  python3 audit-kit/tools/snapshot.py compare [SNAPSHOT_A] [SNAPSHOT_B] [--json] [--audit-dir AUDIT_DIR]

When running 'compare' with one argument, it compares the current active audit with that snapshot.
When running 'compare' with no arguments, it compares the current active audit with the latest snapshot.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys


def get_paths(audit_dir="audit", snapshots_dir=None):
    audit_path = os.path.abspath(audit_dir)
    snaps_path = os.path.abspath(snapshots_dir) if snapshots_dir else os.path.join(audit_path, "snapshots")
    return audit_path, snaps_path


def parse_findings_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def parse_audit_md(path):
    """Fallback parser if findings.json is not present."""
    if not os.path.exists(path):
        return None
    data = {"date": None, "commit": None, "mode": "Unknown", "overall_score": None, "scores": {}, "findings": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        score_match = re.search(r"Overall score:\s*\*\*([0-9.]+)\*\*", content, re.IGNORECASE)
        if score_match:
            data["overall_score"] = float(score_match.group(1))
        commit_match = re.search(r"Commit:\s*`?([a-f0-9]+)`?", content, re.IGNORECASE)
        if commit_match:
            data["commit"] = commit_match.group(1)
        date_match = re.search(r"Date:\s*`?([0-9]{4}-[0-9]{2}-[0-9]{2})`?", content, re.IGNORECASE)
        if date_match:
            data["date"] = date_match.group(1)
    except Exception:
        pass
    return data


def summarize_findings(findings_list):
    summary = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
    if not isinstance(findings_list, list):
        return summary
    for item in findings_list:
        summary["total"] += 1
        sev = str(item.get("severity", "")).lower()
        if sev in summary:
            summary[sev] += 1
    return summary


def calculate_overall_score(scores_dict):
    valid_scores = [v for v in scores_dict.values() if isinstance(v, (int, float))]
    if not valid_scores:
        return None
    return round(sum(valid_scores) / len(valid_scores), 1)


def generate_snapshot_id(date_str, commit_str, snaps_dir):
    now = dt.datetime.now(dt.timezone.utc)
    time_str = now.strftime("%H%M%S")
    clean_date = date_str or now.strftime("%Y-%m-%d")
    clean_commit = commit_str or "uncommitted"
    base_id = f"{clean_date}_{time_str}_{clean_commit}"
    
    candidate = base_id
    counter = 1
    while os.path.exists(os.path.join(snaps_dir, candidate)):
        candidate = f"{base_id}_{counter}"
        counter += 1
    return candidate


def create_snapshot(audit_dir="audit", snapshots_dir=None, name=None, if_exists=False, as_json=False):
    audit_path, snaps_path = get_paths(audit_dir, snapshots_dir)
    findings_path = os.path.join(audit_path, "findings.json")
    audit_md_path = os.path.join(audit_path, "AUDIT.md")
    
    if not os.path.exists(findings_path) and not os.path.exists(audit_md_path):
        if if_exists:
            if as_json:
                print(json.dumps({"status": "skipped", "reason": "no prior audit found"}))
            return 0
        print(f"Error: No prior audit files found in '{audit_dir}' (expected findings.json or AUDIT.md).", file=sys.stderr)
        return 1

    findings_data = parse_findings_json(findings_path) or parse_audit_md(audit_md_path) or {}
    
    date_val = findings_data.get("date")
    commit_val = findings_data.get("commit")
    
    os.makedirs(snaps_path, exist_ok=True)
    snapshot_id = name if name else generate_snapshot_id(date_val, commit_val, snaps_path)
    dest_dir = os.path.join(snaps_path, snapshot_id)
    
    if os.path.exists(dest_dir):
        print(f"Error: Snapshot directory already exists: '{dest_dir}'", file=sys.stderr)
        return 1

    os.makedirs(dest_dir, exist_ok=True)

    copied_files = []
    # Files to copy from audit_dir
    for item in os.listdir(audit_path):
        src_item = os.path.join(audit_path, item)
        # Skip snapshots directory and diff directory
        if os.path.abspath(src_item) == os.path.abspath(snaps_path) or item in ("snapshots", "diff"):
            continue
        dest_item = os.path.join(dest_dir, item)
        if os.path.isfile(src_item):
            shutil.copy2(src_item, dest_item)
            copied_files.append(item)
        elif os.path.isdir(src_item):
            shutil.copytree(src_item, dest_item)
            copied_files.append(f"{item}/")

    # Build snapshot metadata
    scores = findings_data.get("scores", {})
    overall_score = findings_data.get("overall_score")
    if overall_score is None and scores:
        overall_score = calculate_overall_score(scores)
        
    findings_list = findings_data.get("findings", [])
    findings_summary = summarize_findings(findings_list)
    usage_info = findings_data.get("usage", {})
    cost_info = usage_info.get("cost")
    
    metadata = {
        "id": snapshot_id,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "date": date_val or dt.date.today().isoformat(),
        "commit": commit_val or "unknown",
        "branch": findings_data.get("branch", "unknown"),
        "mode": findings_data.get("mode", "Unknown"),
        "tool": findings_data.get("tool", "Unknown"),
        "model": findings_data.get("model", "Unknown"),
        "kit_version": findings_data.get("kit_version", "Unknown"),
        "overall_score": overall_score,
        "dimension_scores": scores,
        "findings_summary": findings_summary,
        "cost": cost_info,
        "tokens": usage_info.get("totals", {}).get("total_tokens"),
        "files": sorted(copied_files)
    }

    meta_file = os.path.join(dest_dir, "snapshot.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    if as_json:
        print(json.dumps({"status": "created", "snapshot": metadata}, indent=2))
    else:
        score_display = f"{overall_score}/10" if overall_score is not None else "N/A"
        print(f"✅ Snapshot created: {snapshot_id}")
        print(f"   Date: {metadata['date']} | Commit: {metadata['commit']} | Mode: {metadata['mode']}")
        print(f"   Score: {score_display} | Findings: {findings_summary['total']} "
              f"(Crit: {findings_summary['critical']}, High: {findings_summary['high']}, "
              f"Med: {findings_summary['medium']}, Low: {findings_summary['low']})")
        print(f"   Location: {dest_dir}")
    return 0


def load_snapshot_metadata(snapshot_dir):
    meta_path = os.path.join(snapshot_dir, "snapshot.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Fallback to reading findings.json inside snapshot dir
    findings_path = os.path.join(snapshot_dir, "findings.json")
    findings = parse_findings_json(findings_path) or {}
    sid = os.path.basename(snapshot_dir)
    scores = findings.get("scores", {})
    return {
        "id": sid,
        "created_at": dt.datetime.fromtimestamp(os.path.getmtime(snapshot_dir), dt.timezone.utc).isoformat(),
        "date": findings.get("date", "Unknown"),
        "commit": findings.get("commit", "Unknown"),
        "branch": findings.get("branch", "unknown"),
        "mode": findings.get("mode", "Unknown"),
        "tool": findings.get("tool", "Unknown"),
        "model": findings.get("model", "Unknown"),
        "kit_version": findings.get("kit_version", "Unknown"),
        "overall_score": findings.get("overall_score") or calculate_overall_score(scores),
        "dimension_scores": scores,
        "findings_summary": summarize_findings(findings.get("findings", [])),
        "cost": findings.get("usage", {}).get("cost"),
        "tokens": findings.get("usage", {}).get("totals", {}).get("total_tokens"),
        "files": os.listdir(snapshot_dir)
    }


def list_snapshots(audit_dir="audit", snapshots_dir=None, as_json=False):
    _, snaps_path = get_paths(audit_dir, snapshots_dir)
    if not os.path.exists(snaps_path):
        if as_json:
            print(json.dumps([]))
        else:
            print("No snapshots directory found.")
        return 0

    snapshots = []
    for entry in sorted(os.listdir(snaps_path)):
        full_path = os.path.join(snaps_path, entry)
        if os.path.isdir(full_path):
            meta = load_snapshot_metadata(full_path)
            snapshots.append(meta)

    # Sort chronologically by created_at or id
    snapshots.sort(key=lambda s: s.get("created_at") or s.get("id"))

    if as_json:
        print(json.dumps(snapshots, indent=2))
        return 0

    if not snapshots:
        print("No audit snapshots available.")
        return 0

    print(f"\nFound {len(snapshots)} audit snapshot(s):\n")
    header = f"{'ID':<30} | {'Date':<10} | {'Commit':<8} | {'Mode':<8} | {'Score':<5} | {'C':<2} | {'H':<2} | {'M':<2} | {'L':<2} | {'Tool'}"
    print(header)
    print("-" * len(header))
    for s in snapshots:
        sum_f = s.get("findings_summary", {})
        score_str = f"{s['overall_score']:.1f}" if s.get("overall_score") is not None else "N/A"
        line = (f"{s['id']:<30} | {str(s.get('date')):<10} | {str(s.get('commit'))[:8]:<8} | "
                f"{str(s.get('mode'))[:8]:<8} | {score_str:<5} | "
                f"{sum_f.get('critical', 0):<2} | {sum_f.get('high', 0):<2} | "
                f"{sum_f.get('medium', 0):<2} | {sum_f.get('low', 0):<2} | "
                f"{str(s.get('tool'))}")
        print(line)
    print()
    return 0


def show_snapshot(snapshot_id, audit_dir="audit", snapshots_dir=None, as_json=False):
    _, snaps_path = get_paths(audit_dir, snapshots_dir)
    snap_dir = os.path.join(snaps_path, snapshot_id)
    if not os.path.exists(snap_dir):
        print(f"Error: Snapshot '{snapshot_id}' not found.", file=sys.stderr)
        return 1

    meta = load_snapshot_metadata(snap_dir)
    if as_json:
        print(json.dumps(meta, indent=2))
        return 0

    sum_f = meta.get("findings_summary", {})
    score_str = f"{meta['overall_score']:.1f}" if meta.get("overall_score") is not None else "N/A"
    print(f"\nSnapshot: {meta['id']}")
    print(f"  Created at : {meta.get('created_at')}")
    print(f"  Date       : {meta.get('date')}")
    print(f"  Commit     : {meta.get('commit')} (branch: {meta.get('branch')})")
    print(f"  Mode       : {meta.get('mode')}")
    print(f"  Tool       : {meta.get('tool')} ({meta.get('model')})")
    print(f"  Kit Version: {meta.get('kit_version')}")
    print(f"  Overall    : {score_str}/10")
    print(f"  Findings   : Total {sum_f.get('total', 0)} (Critical: {sum_f.get('critical', 0)}, "
          f"High: {sum_f.get('high', 0)}, Medium: {sum_f.get('medium', 0)}, Low: {sum_f.get('low', 0)})")
    
    dim_scores = meta.get("dimension_scores", {})
    if dim_scores:
        print("\n  Dimension Scores:")
        for dim, sc in dim_scores.items():
            print(f"    - {dim:<30}: {sc}")
            
    print("\n  Files in snapshot:")
    for f in meta.get("files", []):
        print(f"    - {f}")
    print()
    return 0


def delete_snapshot(snapshot_id, audit_dir="audit", snapshots_dir=None):
    _, snaps_path = get_paths(audit_dir, snapshots_dir)
    snap_dir = os.path.join(snaps_path, snapshot_id)
    if not os.path.exists(snap_dir):
        print(f"Error: Snapshot '{snapshot_id}' not found.", file=sys.stderr)
        return 1
    shutil.rmtree(snap_dir)
    print(f"🗑️ Snapshot '{snapshot_id}' deleted successfully.")
    return 0


def load_audit_data_from_target(target_name, audit_path, snaps_path):
    """Loads findings and scores from either 'current' or a snapshot ID."""
    if target_name in ("current", "active", "latest_active"):
        findings_file = os.path.join(audit_path, "findings.json")
        audit_md = os.path.join(audit_path, "AUDIT.md")
        data = parse_findings_json(findings_file) or parse_audit_md(audit_md) or {}
        data["source"] = "Current Active Audit"
        data["source_id"] = "current"
        return data

    # Check snapshot directory
    snap_dir = os.path.join(snaps_path, target_name)
    if not os.path.exists(snap_dir):
        # Maybe target_name is a prefix or partial match
        matches = [d for d in os.listdir(snaps_path) if d.startswith(target_name)]
        if len(matches) == 1:
            snap_dir = os.path.join(snaps_path, matches[0])
            target_name = matches[0]
        else:
            return None

    findings_file = os.path.join(snap_dir, "findings.json")
    audit_md = os.path.join(snap_dir, "AUDIT.md")
    data = parse_findings_json(findings_file) or parse_audit_md(audit_md) or {}
    data["source"] = f"Snapshot {target_name}"
    data["source_id"] = target_name
    return data


def compare_audits(base_target, current_target="current", audit_dir="audit", snapshots_dir=None, as_json=False):
    audit_path, snaps_path = get_paths(audit_dir, snapshots_dir)

    # If base_target is not provided, pick latest snapshot
    if not base_target:
        if not os.path.exists(snaps_path):
            print("Error: No snapshots available to compare against.", file=sys.stderr)
            return 1
        snaps = sorted([d for d in os.listdir(snaps_path) if os.path.isdir(os.path.join(snaps_path, d))])
        if not snaps:
            print("Error: No snapshots available to compare against.", file=sys.stderr)
            return 1
        base_target = snaps[-1]

    base_data = load_audit_data_from_target(base_target, audit_path, snaps_path)
    if not base_data:
        print(f"Error: Could not load audit data for base target '{base_target}'.", file=sys.stderr)
        return 1

    curr_data = load_audit_data_from_target(current_target, audit_path, snaps_path)
    if not curr_data:
        print(f"Error: Could not load audit data for target '{current_target}'.", file=sys.stderr)
        return 1

    # Score comparison
    base_scores = base_data.get("scores", {})
    curr_scores = curr_data.get("scores", {})
    all_dims = sorted(set(list(base_scores.keys()) + list(curr_scores.keys())))

    base_overall = base_data.get("overall_score") or calculate_overall_score(base_scores)
    curr_overall = curr_data.get("overall_score") or calculate_overall_score(curr_scores)
    
    overall_diff = None
    if base_overall is not None and curr_overall is not None:
        overall_diff = round(curr_overall - base_overall, 2)

    score_diffs = {}
    for dim in all_dims:
        b_sc = base_scores.get(dim)
        c_sc = curr_scores.get(dim)
        delta = None
        if b_sc is not None and c_sc is not None:
            delta = round(c_sc - b_sc, 2)
        score_diffs[dim] = {
            "base": b_sc,
            "target": c_sc,
            "diff": delta
        }

    # Findings comparison
    base_findings = {f.get("id"): f for f in base_data.get("findings", []) if f.get("id")}
    curr_findings = {f.get("id"): f for f in curr_data.get("findings", []) if f.get("id")}

    base_ids = set(base_findings.keys())
    curr_ids = set(curr_findings.keys())

    resolved_ids = sorted(base_ids - curr_ids)
    new_ids = sorted(curr_ids - base_ids)
    persistent_ids = sorted(base_ids & curr_ids)

    resolved_findings = [base_findings[i] for i in resolved_ids]
    new_findings = [curr_findings[i] for i in new_ids]
    persistent_findings = []
    for i in persistent_ids:
        bf = base_findings[i]
        cf = curr_findings[i]
        persistent_findings.append({
            "id": i,
            "title": cf.get("title", bf.get("title", "")),
            "dimension": cf.get("dimension", bf.get("dimension", "")),
            "severity_base": bf.get("severity"),
            "severity_target": cf.get("severity"),
            "severity_changed": bf.get("severity") != cf.get("severity")
        })

    result = {
        "base": {
            "source_id": base_data.get("source_id"),
            "date": base_data.get("date"),
            "commit": base_data.get("commit"),
            "overall_score": base_overall
        },
        "target": {
            "source_id": curr_data.get("source_id"),
            "date": curr_data.get("date"),
            "commit": curr_data.get("commit"),
            "overall_score": curr_overall
        },
        "overall_score_delta": overall_diff,
        "dimension_score_deltas": score_diffs,
        "findings_diff": {
            "resolved_count": len(resolved_findings),
            "new_count": len(new_findings),
            "persistent_count": len(persistent_findings),
            "resolved": resolved_findings,
            "new": new_findings,
            "persistent": persistent_findings
        }
    }

    if as_json:
        print(json.dumps(result, indent=2))
        return 0

    # Human-readable comparison output
    print(f"\n🔍 Audit Comparison: {base_data['source']} ➔ {curr_data['source']}")
    print(f"   Base:   Commit {base_data.get('commit')} ({base_data.get('date')})")
    print(f"   Target: Commit {curr_data.get('commit')} ({curr_data.get('date')})")
    
    diff_symbol = ""
    if overall_diff is not None:
        if overall_diff > 0:
            diff_symbol = f" (+{overall_diff:.1f} 🟢)"
        elif overall_diff < 0:
            diff_symbol = f" ({overall_diff:.1f} 🔴)"
        else:
            diff_symbol = " (= ⚪)"
            
    b_score_str = f"{base_overall:.1f}" if base_overall is not None else "N/A"
    c_score_str = f"{curr_overall:.1f}" if curr_overall is not None else "N/A"
    print(f"\n📊 Overall Score: {b_score_str} ➔ {c_score_str}{diff_symbol}")

    print("\n📈 Dimension Score Deltas:")
    for dim, sinfo in score_diffs.items():
        b_sc = f"{sinfo['base']:.1f}" if sinfo['base'] is not None else "N/A"
        c_sc = f"{sinfo['target']:.1f}" if sinfo['target'] is not None else "N/A"
        diff_str = ""
        if sinfo['diff'] is not None:
            if sinfo['diff'] > 0:
                diff_str = f" (+{sinfo['diff']:.1f})"
            elif sinfo['diff'] < 0:
                diff_str = f" ({sinfo['diff']:.1f})"
            else:
                diff_str = " (=)"
        print(f"   - {dim:<30}: {b_sc} ➔ {c_sc}{diff_str}")

    print(f"\n📋 Findings Evolution:")
    print(f"   🟢 Resolved findings : {len(resolved_findings)}")
    for f in resolved_findings[:10]:
        print(f"      • [{f.get('id')}] ({f.get('severity')}) {f.get('title', '')}")
    if len(resolved_findings) > 10:
        print(f"      ... and {len(resolved_findings) - 10} more")

    print(f"   🔴 New findings      : {len(new_findings)}")
    for f in new_findings[:10]:
        print(f"      • [{f.get('id')}] ({f.get('severity')}) {f.get('title', '')}")
    if len(new_findings) > 10:
        print(f"      ... and {len(new_findings) - 10} more")

    print(f"   🟡 Persistent findings: {len(persistent_findings)}")
    for f in persistent_findings[:5]:
        sev_change = f" ({f['severity_base']} ➔ {f['severity_target']})" if f['severity_changed'] else f" ({f['severity_target']})"
        print(f"      • [{f.get('id')}]{sev_change} {f.get('title', '')}")
    if len(persistent_findings) > 5:
        print(f"      ... and {len(persistent_findings) - 5} more")

    print()
    return 0


def main():
    parser = argparse.ArgumentParser(description="Audit snapshot management and comparison tool.")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Create command
    p_create = subparsers.add_parser("create", help="Create a snapshot of the current audit directory")
    p_create.add_argument("--name", help="Custom name for the snapshot")
    p_create.add_argument("--audit-dir", default="audit", help="Path to audit directory (default: audit)")
    p_create.add_argument("--snapshots-dir", help="Path to snapshots directory")
    p_create.add_argument("--if-exists", action="store_true", help="Quietly exit 0 if no prior audit exists")
    p_create.add_argument("--json", action="store_true", help="Output result as JSON")

    # List command
    p_list = subparsers.add_parser("list", help="List all historical snapshots")
    p_list.add_argument("--audit-dir", default="audit", help="Path to audit directory (default: audit)")
    p_list.add_argument("--snapshots-dir", help="Path to snapshots directory")
    p_list.add_argument("--json", action="store_true", help="Output snapshots list as JSON")

    # Show command
    p_show = subparsers.add_parser("show", help="Show details of a snapshot")
    p_show.add_argument("snapshot_id", help="Snapshot identifier")
    p_show.add_argument("--audit-dir", default="audit", help="Path to audit directory (default: audit)")
    p_show.add_argument("--snapshots-dir", help="Path to snapshots directory")
    p_show.add_argument("--json", action="store_true", help="Output details as JSON")

    # Delete command
    p_del = subparsers.add_parser("delete", help="Delete a snapshot")
    p_del.add_argument("snapshot_id", help="Snapshot identifier")
    p_del.add_argument("--audit-dir", default="audit", help="Path to audit directory (default: audit)")
    p_del.add_argument("--snapshots-dir", help="Path to snapshots directory")

    # Compare command
    p_cmp = subparsers.add_parser("compare", help="Compare current audit with a snapshot or two snapshots")
    p_cmp.add_argument("base", nargs="?", default=None, help="Base snapshot ID (default: latest snapshot)")
    p_cmp.add_argument("target", nargs="?", default="current", help="Target snapshot ID or 'current' (default: current)")
    p_cmp.add_argument("--audit-dir", default="audit", help="Path to audit directory (default: audit)")
    p_cmp.add_argument("--snapshots-dir", help="Path to snapshots directory")
    p_cmp.add_argument("--json", action="store_true", help="Output comparison result as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "create":
        return create_snapshot(
            audit_dir=args.audit_dir,
            snapshots_dir=args.snapshots_dir,
            name=args.name,
            if_exists=args.if_exists,
            as_json=args.json
        )
    elif args.command == "list":
        return list_snapshots(
            audit_dir=args.audit_dir,
            snapshots_dir=args.snapshots_dir,
            as_json=args.json
        )
    elif args.command == "show":
        return show_snapshot(
            snapshot_id=args.snapshot_id,
            audit_dir=args.audit_dir,
            snapshots_dir=args.snapshots_dir,
            as_json=args.json
        )
    elif args.command == "delete":
        return delete_snapshot(
            snapshot_id=args.snapshot_id,
            audit_dir=args.audit_dir,
            snapshots_dir=args.snapshots_dir
        )
    elif args.command == "compare":
        return compare_audits(
            base_target=args.base,
            current_target=args.target,
            audit_dir=args.audit_dir,
            snapshots_dir=args.snapshots_dir,
            as_json=args.json
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
