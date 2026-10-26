#!/usr/bin/env python3
"""Unit tests for tools/snapshot.py."""
import json
import os
import shutil
import tempfile
import unittest

from tools.snapshot import (
    create_snapshot,
    list_snapshots,
    show_snapshot,
    compare_audits,
    delete_snapshot,
    summarize_findings,
    calculate_overall_score
)


class TestSnapshotTool(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.audit_dir = os.path.join(self.test_dir, "audit")
        self.snapshots_dir = os.path.join(self.audit_dir, "snapshots")
        os.makedirs(self.audit_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_create_snapshot_empty_without_if_exists(self):
        code = create_snapshot(audit_dir=self.audit_dir, snapshots_dir=self.snapshots_dir, if_exists=False)
        self.assertEqual(code, 1)

    def test_create_snapshot_empty_with_if_exists(self):
        code = create_snapshot(audit_dir=self.audit_dir, snapshots_dir=self.snapshots_dir, if_exists=True)
        self.assertEqual(code, 0)

    def test_create_and_list_snapshot(self):
        findings_data = {
            "date": "2026-10-26",
            "commit": "abc1234",
            "branch": "main",
            "mode": "Standard",
            "tool": "Antigravity",
            "model": "gemini-1.5-pro",
            "kit_version": "2.8.1",
            "scores": {
                "Maintainability": 8.0,
                "Security": 9.0
            },
            "findings": [
                {"id": "SEC-001", "severity": "High", "title": "Insecure key storage"},
                {"id": "MNT-001", "severity": "Low", "title": "Missing docstrings"}
            ]
        }
        with open(os.path.join(self.audit_dir, "findings.json"), "w") as f:
            json.dump(findings_data, f)
        with open(os.path.join(self.audit_dir, "AUDIT.md"), "w") as f:
            f.write("# Executive Summary\nOverall score: **8.5**\n")
        with open(os.path.join(self.audit_dir, "security.md"), "w") as f:
            f.write("# Security Report\n")

        # Create named snapshot
        code = create_snapshot(
            audit_dir=self.audit_dir,
            snapshots_dir=self.snapshots_dir,
            name="snap_test_1"
        )
        self.assertEqual(code, 0)

        snap_path = os.path.join(self.snapshots_dir, "snap_test_1")
        self.assertTrue(os.path.isdir(snap_path))
        self.assertTrue(os.path.isfile(os.path.join(snap_path, "snapshot.json")))
        self.assertTrue(os.path.isfile(os.path.join(snap_path, "findings.json")))
        self.assertTrue(os.path.isfile(os.path.join(snap_path, "AUDIT.md")))
        self.assertTrue(os.path.isfile(os.path.join(snap_path, "security.md")))

        with open(os.path.join(snap_path, "snapshot.json")) as f:
            meta = json.load(f)
        self.assertEqual(meta["commit"], "abc1234")
        self.assertEqual(meta["overall_score"], 8.5)
        self.assertEqual(meta["findings_summary"]["total"], 2)
        self.assertEqual(meta["findings_summary"]["high"], 1)
        self.assertEqual(meta["findings_summary"]["low"], 1)

    def test_compare_audits(self):
        # Base snapshot
        snap1_data = {
            "date": "2026-10-20",
            "commit": "base001",
            "scores": {"Maintainability": 7.0, "Security": 7.0},
            "overall_score": 7.0,
            "findings": [
                {"id": "SEC-001", "severity": "High", "title": "Old bug to resolve"},
                {"id": "MNT-001", "severity": "Low", "title": "Persistent bug"}
            ]
        }
        snap1_dir = os.path.join(self.snapshots_dir, "snap_base")
        os.makedirs(snap1_dir, exist_ok=True)
        with open(os.path.join(snap1_dir, "findings.json"), "w") as f:
            json.dump(snap1_data, f)

        # Target (active audit)
        curr_data = {
            "date": "2026-10-26",
            "commit": "curr002",
            "scores": {"Maintainability": 8.0, "Security": 9.0},
            "overall_score": 8.5,
            "findings": [
                {"id": "MNT-001", "severity": "Medium", "title": "Persistent bug escalated"},
                {"id": "SEC-002", "severity": "Critical", "title": "New SQL injection"}
            ]
        }
        with open(os.path.join(self.audit_dir, "findings.json"), "w") as f:
            json.dump(curr_data, f)

        # Run compare
        code = compare_audits(
            base_target="snap_base",
            current_target="current",
            audit_dir=self.audit_dir,
            snapshots_dir=self.snapshots_dir,
            as_json=False
        )
        self.assertEqual(code, 0)

    def test_delete_snapshot(self):
        snap_dir = os.path.join(self.snapshots_dir, "to_delete")
        os.makedirs(snap_dir, exist_ok=True)
        self.assertTrue(os.path.exists(snap_dir))

        code = delete_snapshot("to_delete", audit_dir=self.audit_dir, snapshots_dir=self.snapshots_dir)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(snap_dir))


if __name__ == "__main__":
    unittest.main()
