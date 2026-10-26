#!/usr/bin/env python3
"""Unit tests for tools/cvss.py implementing FIRST.org reference vectors."""
import os
import json
import tempfile
import unittest
from tools.cvss import (
    score_vector_string,
    cvss_roundup,
    extract_cvss_vector,
    enrich_finding,
    enrich_findings_list,
)


class TestCVSS(unittest.TestCase):
    def test_roundup(self):
        self.assertEqual(cvss_roundup(4.0), 4.0)
        self.assertEqual(cvss_roundup(4.02), 4.1)
        self.assertEqual(cvss_roundup(4.0001), 4.1)
        self.assertEqual(cvss_roundup(4.1), 4.1)

    def test_heartbleed_cve_2014_0160(self):
        # Heartbleed: Network, Low, None, None, Scope Unchanged, High Confidentiality
        res = score_vector_string("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N")
        self.assertEqual(res["score"], 7.5)
        self.assertEqual(res["rating"], "High")

    def test_maximum_critical_vector(self):
        res = score_vector_string("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        self.assertEqual(res["score"], 9.8)
        self.assertEqual(res["rating"], "Critical")

    def test_scope_changed_critical_vector(self):
        # Scope changed RCE
        res = score_vector_string("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H")
        self.assertEqual(res["score"], 10.0)
        self.assertEqual(res["rating"], "Critical")

    def test_xss_scope_changed(self):
        # Stored / Reflected XSS with Scope Changed
        res = score_vector_string("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N")
        self.assertEqual(res["score"], 6.1)
        self.assertEqual(res["rating"], "Medium")

    def test_zero_impact_vector(self):
        res = score_vector_string("CVSS:3.1/AV:P/AC:H/PR:H/UI:R/S:U/C:N/I:N/A:N")
        self.assertEqual(res["score"], 0.0)
        self.assertEqual(res["rating"], "None")

    def test_extract_and_enrich_finding_string(self):
        finding = {
            "id": "SEC-001",
            "cvss": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        }
        enrich_finding(finding)
        self.assertIsInstance(finding["cvss"], dict)
        self.assertEqual(finding["cvss"]["score"], 9.8)
        self.assertEqual(finding["cvss"]["rating"], "Critical")

    def test_extract_from_description(self):
        finding = {
            "id": "SEC-002",
            "description": "SQL Injection found. CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N present in app."
        }
        enrich_finding(finding)
        self.assertIn("cvss", finding)
        self.assertEqual(finding["cvss"]["score"], 7.5)

    def test_batch_enrich_findings_list(self):
        findings = [
            {"id": "SEC-001", "cvss": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"},
            {"id": "SEC-002", "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N"},
            {"id": "REL-001", "title": "No CVSS"}
        ]
        enrich_findings_list(findings)
        self.assertEqual(findings[0]["cvss"]["score"], 9.8)
        self.assertEqual(findings[1]["cvss"]["score"], 6.1)
        self.assertNotIn("cvss", findings[2])


if __name__ == "__main__":
    unittest.main()
