# SKILL.md Assignment
### Research + Industry Demo — Healthcare Report Generator

---

## What is SKILL.md?

A `SKILL.md` is a structured Markdown file that gives Claude AI
domain-specific workflows, knowledge, and tool patterns.

**Structure of every skill:**
```
skill/
├── SKILL.md          ← Instructions + YAML trigger metadata
├── scripts/          ← Python/bash helpers
├── references/       ← Domain knowledge (codes, standards)
└── assets/           ← Templates, headers
```

**3-Layer Loading:**
```
Layer 1 → Metadata (name + description)   always in context
Layer 2 → SKILL.md body                   loaded on trigger
Layer 3 → scripts / references / assets   loaded on demand
```

---

## Industry Chosen: Healthcare

**Why?**
- Clinicians spend 35–55% of time on documentation
- Strict formats required: SOAP notes, ICD-10, HIPAA
- Errors are costly — missing fields = patient safety risk
- Perfect fit: standardised output + domain lookup + validation

---

## Project Structure

```
skillmd-assignment/
│
├── README.md                        ← You are here
│
├── skill/                           ← The SKILL.md package
│   ├── SKILL.md                     ← Core skill definition
│   ├── scripts/
│   │   └── generate_report.py       ← Report generator (Python)
│   ├── references/
│   │   └── icd10_common.md          ← ICD-10 code lookup table
│   └── assets/
│       └── report_header.txt        ← Header template
│
├── demo/
│   ├── run_demo.py                  ← Run this to see output
│   ├── sample_input.json            ← Example patient data
│   └── sample_output.txt            ← Generated report
│
├── tests/
│   └── test_skill.py                ← 19 unit tests (all pass)
│
└── docs/
    └── research.md                  ← Full research notes
```

---

## How to Run

```bash
# Run the demo
python3 demo/run_demo.py

# Run tests
python3 tests/test_skill.py
```

---

## Sample Output

```
════════════════════════════════════════════════════════
    CLINICAL PATIENT REPORT  [FINAL]
    Koramangala Medical Centre, Bengaluru
    Generated : 2026-06-24
    Provider  : Dr. Sunita Rao
    CONFIDENTIAL — HIPAA Protected Health Information
════════════════════════════════════════════════════════

PATIENT  : Arjun Mehta | DOB: 1981-11-23 | MRN: KMC-20048

── SUBJECTIVE ──────────────────────────────────────────
Chief Complaint : Chest tightness, shortness of breath

── OBJECTIVE ────────────────────────────────────────────
  Blood Pressure : 148/92 mmHg
  Heart Rate     : 88 bpm

── ASSESSMENT ───────────────────────────────────────────
Primary Dx : Angina pectoris | ICD-10: I20.9

── PLAN ─────────────────────────────────────────────────
  1. ECG stat
  2. Troponin q6h
  3. Aspirin 325mg stat
════════════════════════════════════════════════════════
```
