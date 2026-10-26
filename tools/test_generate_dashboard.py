#!/usr/bin/env python3
"""Unit tests for tools/generate_dashboard.py."""
import json
import os
import shutil
import tempfile
import unittest

from tools.generate_dashboard import generate_dashboard


class TestGenerateDashboard(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.audit_dir = os.path.join(self.test_dir, "audit")
        self.snaps_dir = os.path.join(self.audit_dir, "snapshots")
        os.makedirs(self.snaps_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_generate_dashboard_with_findings_and_snapshots(self):
        findings_data = {
            "project": "test-repo",
            "date": "2026-10-26",
            "commit": "deadbeef",
            "mode": "Standard",
            "overall_score": 8.5,
            "scores": {"Maintainability": 8.0, "Security": 9.0},
            "findings": [
                {"id": "SEC-001", "severity": "High", "title": "SQL Injection in auth", "dimension": "Security", "file": "src/auth.py", "line": 42}
            ]
        }
        with open(os.path.join(self.audit_dir, "findings.json"), "w") as f:
            json.dump(findings_data, f)

        # Add a dummy snapshot
        snap1_dir = os.path.join(self.snaps_dir, "snap1")
        os.makedirs(snap1_dir, exist_ok=True)
        with open(os.path.join(snap1_dir, "findings.json"), "w") as f:
            json.dump({"date": "2026-10-20", "commit": "old001", "overall_score": 7.0, "findings": []}, f)
        with open(os.path.join(snap1_dir, "snapshot.json"), "w") as f:
            json.dump({"id": "snap1", "date": "2026-10-20", "commit": "old001", "overall_score": 7.0}, f)

        output_file = os.path.join(self.audit_dir, "dashboard.html")
        code = generate_dashboard(audit_dir=self.audit_dir, output_path=output_file)
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(output_file))

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("test-repo", content)
        self.assertIn("SEC-001", content)
        self.assertIn("SQL Injection in auth", content)
        self.assertIn("Estimated Cost", content)
        self.assertIn("snap1", content)
        self.assertIn("<!DOCTYPE html>", content)


if __name__ == "__main__":
    unittest.main()
