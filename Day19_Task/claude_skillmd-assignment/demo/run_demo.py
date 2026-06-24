#!/usr/bin/env python3
"""
run_demo.py — Demonstrates the healthcare-report SKILL.md

Run from project root:
    python3 demo/run_demo.py
"""

import json, sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../skill/scripts"))
from generate_report import generate_report

def main():
    print("=" * 56)
    print("  SKILL.md Demo — healthcare-report")
    print("  Industry: Healthcare / Clinical Documentation")
    print("=" * 56)

    input_file = os.path.join(os.path.dirname(__file__), "sample_input.json")
    with open(input_file) as f:
        data = json.load(f)

    print(f"\nPatient: {data['patient_name']}")
    print("Generating SOAP report...\n")

    report = generate_report(data)
    print(report)

    output_file = os.path.join(os.path.dirname(__file__), "sample_output.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print("[OK] Report saved -> demo/sample_output.txt")
    print("\nSKILL.md steps executed:")
    print("  [1] Required fields validated")
    print("  [2] ICD-10 code applied from references/icd10_common.md")
    print("  [3] SOAP structure enforced")
    print("  [4] HIPAA confidentiality header included")
    print("  [5] Plan formatted as numbered list")

if __name__ == "__main__":
    main()
