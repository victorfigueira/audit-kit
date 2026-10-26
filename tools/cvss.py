#!/usr/bin/env python3
"""CVSS v3.1 Base Score calculator, parser, and validator.

Implements the official FIRST.org CVSS v3.1 specification:
https://www.first.org/cvss/v3.1/specification-document

Usage (from project root):
  python3 audit-kit/tools/cvss.py "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
  python3 audit-kit/tools/cvss.py --json "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"
"""
import argparse
import json
import math
import re
import sys

# Metrics weight constants per FIRST.org CVSS v3.1 Specification
AV_WEIGHTS = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
AC_WEIGHTS = {"L": 0.77, "H": 0.44}
PR_WEIGHTS = {
    "U": {"N": 0.85, "L": 0.62, "H": 0.27},  # Scope Unchanged
    "C": {"N": 0.85, "L": 0.68, "H": 0.50},  # Scope Changed
}
UI_WEIGHTS = {"N": 0.85, "R": 0.62}
CIA_WEIGHTS = {"N": 0.00, "L": 0.22, "H": 0.56}

METRIC_LABELS = {
    "AV": {"N": "Network", "A": "Adjacent", "L": "Local", "P": "Physical"},
    "AC": {"L": "Low", "H": "High"},
    "PR": {"N": "None", "L": "Low", "H": "High"},
    "UI": {"N": "None", "R": "Required"},
    "S":  {"U": "Unchanged", "C": "Changed"},
    "C":  {"N": "None", "L": "Low", "H": "High"},
    "I":  {"N": "None", "L": "Low", "H": "High"},
    "A":  {"N": "None", "L": "Low", "H": "High"},
}


def cvss_roundup(input_val):
    """Official FIRST.org CVSS v3.1 Roundup function.

    Roundup is defined as the smallest number, specified to one decimal place,
    that is greater than or equal to the input number.
    """
    int_input = round(input_val * 100000.0)
    if int_input % 10000 == 0:
        return int_input / 100000.0
    return (math.floor(int_input / 10000.0) + 1.0) / 10.0


def get_rating(score):
    if score == 0.0:
        return "None"
    elif score < 4.0:
        return "Low"
    elif score < 7.0:
        return "Medium"
    elif score < 9.0:
        return "High"
    else:
        return "Critical"


def parse_vector(vector_str):
    """Parse and validate CVSS v3.1 vector string."""
    clean = vector_str.strip()
    if clean.startswith("CVSS:3.1/"):
        clean = clean[len("CVSS:3.1/"):]
    elif clean.startswith("CVSS:3.0/"):
        clean = clean[len("CVSS:3.0/"):]

    parts = clean.split("/")
    metrics = {}
    for part in parts:
        if ":" in part:
            k, v = part.split(":", 1)
            metrics[k.upper()] = v.upper()

    required = ["AV", "AC", "PR", "UI", "S", "C", "I", "A"]
    missing = [m for m in required if m not in metrics]
    if missing:
        raise ValueError(f"Missing required CVSS metrics: {missing}")

    # Validate values
    if metrics["AV"] not in AV_WEIGHTS:
        raise ValueError(f"Invalid Attack Vector (AV): {metrics['AV']}")
    if metrics["AC"] not in AC_WEIGHTS:
        raise ValueError(f"Invalid Attack Complexity (AC): {metrics['AC']}")
    if metrics["UI"] not in UI_WEIGHTS:
        raise ValueError(f"Invalid User Interaction (UI): {metrics['UI']}")
    if metrics["S"] not in ("U", "C"):
        raise ValueError(f"Invalid Scope (S): {metrics['S']}")
    if metrics["PR"] not in ("N", "L", "H"):
        raise ValueError(f"Invalid Privileges Required (PR): {metrics['PR']}")
    for impact in ("C", "I", "A"):
        if metrics[impact] not in CIA_WEIGHTS:
            raise ValueError(f"Invalid {impact} impact: {metrics[impact]}")

    return metrics


def calculate_cvss_31(metrics):
    """Calculate CVSS v3.1 Base Score from metrics dict."""
    av = AV_WEIGHTS[metrics["AV"]]
    ac = AC_WEIGHTS[metrics["AC"]]
    scope = metrics["S"]
    pr = PR_WEIGHTS[scope][metrics["PR"]]
    ui = UI_WEIGHTS[metrics["UI"]]
    c = CIA_WEIGHTS[metrics["C"]]
    i = CIA_WEIGHTS[metrics["I"]]
    a = CIA_WEIGHTS[metrics["A"]]

    # Impact Sub-Score (ISS)
    iss = 1.0 - ((1.0 - c) * (1.0 - i) * (1.0 - a))

    # Impact
    if scope == "U":
        impact = 6.42 * iss
    else:  # Scope Changed
        impact = 7.52 * (iss - 0.029) - 3.25 * ((iss - 0.02) ** 15)

    # Exploitability
    exploitability = 8.22 * av * ac * pr * ui

    # Base Score
    if impact <= 0:
        base_score = 0.0
    else:
        if scope == "U":
            base_score = cvss_roundup(min(impact + exploitability, 10.0))
        else:
            base_score = cvss_roundup(min(1.08 * (impact + exploitability), 10.0))

    base_score = round(base_score, 1)
    rating = get_rating(base_score)

    canonical_vector = (
        f"CVSS:3.1/AV:{metrics['AV']}/AC:{metrics['AC']}/PR:{metrics['PR']}/"
        f"UI:{metrics['UI']}/S:{metrics['S']}/C:{metrics['C']}/I:{metrics['I']}/A:{metrics['A']}"
    )

    human_metrics = {k: METRIC_LABELS[k][metrics[k]] for k in metrics if k in METRIC_LABELS}

    return {
        "version": "3.1",
        "vector": canonical_vector,
        "score": base_score,
        "rating": rating,
        "impact_subscore": round(iss, 3),
        "impact": round(impact, 3),
        "exploitability": round(exploitability, 3),
        "metrics": human_metrics
    }


def score_vector_string(vector_str):
    metrics = parse_vector(vector_str)
    return calculate_cvss_31(metrics)


def main():
    parser = argparse.ArgumentParser(description="CVSS v3.1 calculator and validator.")
    parser.add_argument("vector", help="CVSS v3.1 vector string (e.g. CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    try:
        res = score_vector_string(args.vector)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"CVSS v3.1 Base Score: {res['score']} ({res['rating']})")
            print(f"Vector: {res['vector']}")
            print("Metrics:")
            for k, v in res["metrics"].items():
                print(f"  - {k}: {v}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
