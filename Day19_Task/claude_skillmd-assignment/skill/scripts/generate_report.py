#!/usr/bin/env python3
"""
generate_report.py
Script for healthcare-report SKILL.md.
Generates a SOAP-format clinical patient report.

CLI usage:
    python3 generate_report.py --patient-name "John Doe" --dob "1985-03-12" \
        --mrn "001" --provider "Dr. X" --complaint "Fever" \
        --vitals "BP:120/80,HR:72,Temp:38.5,SpO2:98,Weight:65" \
        --assessment "Viral fever | ICD-10: B34.9" --plan "Rest; Fluids"

Python API:
    from generate_report import generate_report
    report = generate_report({ "patient_name": "John Doe", ... })
"""

import argparse
import sys
from datetime import date

SEP  = "═" * 56
LINE = "─"

REQUIRED = ["patient_name", "dob", "mrn", "provider", "complaint", "assessment", "plan"]


def parse_vitals(s):
    """'BP:120/80,HR:72' → {'BP': '120/80', 'HR': '72'}"""
    if not s:
        return {}
    return {k.strip().upper(): v.strip()
            for item in s.split(",") if ":" in item
            for k, _, v in [item.partition(":")]}


def validate(data):
    return [f for f in REQUIRED if not data.get(f, "").strip()]


def numbered_list(s):
    items = [i.strip() for i in s.split(";") if i.strip()]
    return "\n".join(f"  {n+1}. {item}" for n, item in enumerate(items))


def generate_report(data):
    """Generate formatted SOAP report. Raises ValueError on missing fields."""
    missing = validate(data)
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    v      = parse_vitals(data.get("vitals", ""))
    today  = data.get("report_date", str(date.today()))
    status = "DRAFT" if data.get("draft") else "FINAL"
    fac    = data.get("facility", "General Hospital")

    lines = [
        "", SEP,
        f"    CLINICAL PATIENT REPORT  [{status}]",
        f"    {fac}",
        f"    Generated : {today}",
        f"    Provider  : {data['provider']}",
        "    CONFIDENTIAL - HIPAA Protected Health Information",
        SEP, "",
        f"PATIENT  : {data['patient_name']}",
        f"DOB      : {data['dob']}",
        f"MRN      : {data['mrn']}",
        f"ALLERGIES: {data.get('allergies', 'NKDA - No Known Drug Allergies')}",
        "",
        f"── SUBJECTIVE {LINE*43}",
        f"Chief Complaint : {data['complaint']}",
    ]

    if data.get("hpi"): lines.append(f"History (HPI)   : {data['hpi']}")
    if data.get("pmh"): lines.append(f"Past Med Hx     : {data['pmh']}")

    lines += ["", f"── OBJECTIVE {LINE*44}"]
    if v:
        lines.append("Vital Signs:")
        for key, label, unit in [
            ("BP",     "Blood Pressure", "mmHg"),
            ("HR",     "Heart Rate",     "bpm"),
            ("TEMP",   "Temperature",    "°C"),
            ("SPO2",   "SpO2",           "%"),
            ("WEIGHT", "Weight",         "kg"),
        ]:
            if key in v:
                lines.append(f"  {label:<15}: {v[key]} {unit}")
    else:
        lines.append("  Vitals: Not recorded")

    if data.get("exam_findings"):
        lines.append(f"Physical Exam   : {data['exam_findings']}")

    lines += [
        "", f"── ASSESSMENT {LINE*43}",
        f"Primary Dx : {data['assessment']}",
    ]
    if data.get("secondary_dx"):
        lines.append(f"Secondary  : {data['secondary_dx']}")

    lines += ["", f"── PLAN {LINE*49}", numbered_list(data["plan"])]

    if data.get("follow_up") or data.get("referral"):
        lines += ["", f"── FOLLOW-UP {LINE*44}"]
        if data.get("follow_up"):  lines.append(f"  Return Visit : {data['follow_up']}")
        if data.get("referral"):   lines.append(f"  Referring To : {data['referral']}")

    lines += ["", SEP, f"    END OF REPORT - {data['provider']} | {today}", SEP, ""]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="Generate a SOAP clinical patient report.")
    p.add_argument("--patient-name", required=True)
    p.add_argument("--dob",          required=True)
    p.add_argument("--mrn",          required=True)
    p.add_argument("--provider",     required=True)
    p.add_argument("--complaint",    required=True)
    p.add_argument("--assessment",   required=True)
    p.add_argument("--plan",         required=True)
    p.add_argument("--vitals",    default="")
    p.add_argument("--allergies", default="NKDA")
    p.add_argument("--hpi",       default="")
    p.add_argument("--pmh",       default="")
    p.add_argument("--facility",  default="General Hospital")
    p.add_argument("--follow-up", default="")
    p.add_argument("--referral",  default="")
    p.add_argument("--output",    default="")
    p.add_argument("--draft",     action="store_true")
    args = p.parse_args()

    data = {k.replace("-", "_"): v for k, v in vars(args).items()}
    data["patient_name"] = args.patient_name

    try:
        report = generate_report(data)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Saved to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
