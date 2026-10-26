#!/usr/bin/env python3
"""Unit tests for cost calculation and usage reporting."""
import unittest
from tools.usage_report import compute_cost, match_model_pricing


class TestUsageCost(unittest.TestCase):
    def test_model_matching(self):
        self.assertEqual(match_model_pricing("claude-opus-5-5")["input"], 15.00)
        self.assertEqual(match_model_pricing("claude-3-5-sonnet")["input"], 3.00)
        self.assertEqual(match_model_pricing("claude-3-5-haiku")["input"], 0.80)
        self.assertEqual(match_model_pricing("Gemini 2.5 Pro")["input"], 1.25)
        self.assertEqual(match_model_pricing("Gemini 2.0 Flash")["input"], 0.10)
        self.assertEqual(match_model_pricing("gpt-4o")["input"], 2.50)
        self.assertEqual(match_model_pricing("unknown-llm")["input"], 3.00)

    def test_compute_cost_claude(self):
        totals = {
            "input_tokens": 1_000_000,
            "output_tokens": 100_000,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 500_000
        }
        cost = compute_cost(totals, ["claude-3-5-sonnet"])
        # in: 1.0 * 3.0 = $3.00
        # out: 0.1 * 15.0 = $1.50
        # cache_read: 0.5 * 0.30 = $0.15
        # total = $4.65
        self.assertAlmostEqual(cost["total_usd"], 4.65, places=2)
        self.assertEqual(cost["formatted"], "$4.65")
        self.assertEqual(cost["currency"], "USD")

    def test_compute_cost_zero(self):
        totals = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
        cost = compute_cost(totals, ["claude-3-5-sonnet"])
        self.assertEqual(cost["total_usd"], 0.0)
        self.assertEqual(cost["formatted"], "$0.00")


if __name__ == "__main__":
    unittest.main()
