#!/usr/bin/env python3
"""Generate an interactive, standalone, zero-dependency HTML dashboard for audit-kit.

Usage (from project root):
  python3 audit-kit/tools/generate_dashboard.py [--audit-dir AUDIT_DIR] [--output OUTPUT_PATH] [--open]

Outputs:
  audit/dashboard.html (openable in any browser without local server or CDN internet connection)
"""
import argparse
import json
import os
import sys
import webbrowser


def load_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def collect_snapshots(snapshots_dir):
    if not os.path.exists(snapshots_dir):
        return []
    snapshots = []
    for entry in sorted(os.listdir(snapshots_dir)):
        snap_path = os.path.join(snapshots_dir, entry)
        if not os.path.isdir(snap_path):
            continue
        meta_file = os.path.join(snap_path, "snapshot.json")
        meta = load_json(meta_file)
        findings_file = os.path.join(snap_path, "findings.json")
        findings_data = load_json(findings_file) or {}
        
        if not meta:
            meta = {
                "id": entry,
                "date": findings_data.get("date", "Unknown"),
                "commit": findings_data.get("commit", "Unknown"),
                "overall_score": findings_data.get("overall_score"),
                "mode": findings_data.get("mode", "Standard"),
                "tool": findings_data.get("tool", "Unknown"),
                "findings_summary": {"total": len(findings_data.get("findings", []))}
            }
        
        # Include list of findings for diff comparison
        meta["findings"] = findings_data.get("findings", [])
        snapshots.append(meta)
    
    # Sort chronologically
    snapshots.sort(key=lambda s: s.get("created_at") or s.get("id"))
    return snapshots


def generate_dashboard(audit_dir="audit", template_path=None, output_path=None, open_browser=False):
    audit_path = os.path.abspath(audit_dir)
    findings_file = os.path.join(audit_path, "findings.json")
    audit_data = load_json(findings_file)

    if not audit_data:
        # Check if AUDIT.md exists
        audit_md = os.path.join(audit_path, "AUDIT.md")
        if not os.path.exists(audit_md):
            print(f"Error: No audit results found in '{audit_dir}'. Run an audit first.", file=sys.stderr)
            return 1
        audit_data = {
            "project": os.path.basename(os.path.abspath(".")),
            "date": "Recent",
            "mode": "Standard",
            "scores": {},
            "findings": []
        }

    # Ensure project name
    if not audit_data.get("project"):
        audit_data["project"] = os.path.basename(os.path.abspath("."))

    # Collect snapshots
    snaps_dir = os.path.join(audit_path, "snapshots")
    audit_data["snapshots"] = collect_snapshots(snaps_dir)

    # Resolve template
    if not template_path:
        # Check adjacent templates directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidate = os.path.join(script_dir, "..", "templates", "dashboard.html")
        if os.path.exists(candidate):
            template_path = candidate
        elif os.path.exists("templates/dashboard.html"):
            template_path = "templates/dashboard.html"
        elif os.path.exists("audit-kit/templates/dashboard.html"):
            template_path = "audit-kit/templates/dashboard.html"
        else:
            print("Error: Could not locate 'dashboard.html' template.", file=sys.stderr)
            return 1

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    except Exception as e:
        print(f"Error reading template '{template_path}': {e}", file=sys.stderr)
        return 1

    # Inject data payload safely
    json_payload = json.dumps(audit_data, indent=2, ensure_ascii=False)
    # Escape closing script tag if any in payload
    json_payload = json_payload.replace("</script>", "<\\/script>")

    rendered = template_content.replace("__AUDIT_DATA_PLACEHOLDER__", json_payload)

    # Determine output path
    if not output_path:
        output_path = os.path.join(audit_path, "dashboard.html")
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"✅ Dashboard generated successfully: {output_path}")
    print(f"   Project: {audit_data.get('project')} | Findings: {len(audit_data.get('findings', []))} | Snapshots: {len(audit_data.get('snapshots', []))}")
    print(f"   Open in browser: file://{os.path.abspath(output_path)}")

    if open_browser:
        webbrowser.open(f"file://{os.path.abspath(output_path)}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Generate interactive HTML dashboard for audit-kit.")
    parser.add_argument("--audit-dir", default="audit", help="Directory containing audit results (default: audit)")
    parser.add_argument("--template", help="Path to custom dashboard.html template")
    parser.add_argument("--output", help="Path to write dashboard.html (default: <audit-dir>/dashboard.html)")
    parser.add_argument("--open", action="store_true", help="Open generated dashboard in default browser")

    args = parser.parse_args()
    return generate_dashboard(
        audit_dir=args.audit_dir,
        template_path=args.template,
        output_path=args.output,
        open_browser=args.open
    )


if __name__ == "__main__":
    sys.exit(main())
