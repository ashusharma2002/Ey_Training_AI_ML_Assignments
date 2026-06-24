---
name: healthcare-report
description: >
  Use this skill whenever a user wants to generate a clinical patient report,
  SOAP note, discharge summary, or any structured medical documentation.
  Triggers: 'patient report', 'SOAP note', 'clinical note', 'discharge summary',
  'medical report'. Also triggers when user provides patient vitals or symptoms
  and asks for a formatted document — even if they just say 'write up this patient'.
  Always use when clinical data needs to be turned into a structured professional
  document with ICD-10 codes and HIPAA compliance.
compatibility:
  python: ">=3.8"
---

# Healthcare Report Skill

Generates HIPAA-aware clinical patient reports in SOAP format
with ICD-10 coded diagnoses.

---

## Workflow

### Step 1 — Check Required Fields

Verify the user has provided all of these (ask if missing):

| Field          | Required | Notes                        |
|----------------|----------|------------------------------|
| Patient name   | ✅        | First + Last                 |
| Date of birth  | ✅        | YYYY-MM-DD                   |
| MRN            | ✅        | Any unique patient ID        |
| Chief complaint| ✅        | Primary reason for visit     |
| Vital signs    | ✅        | At minimum BP + HR           |
| Provider name  | ✅        | Attending physician          |
| Assessment     | ✅        | Diagnosis (free text or code)|
| Plan           | ✅        | At least one action item     |
| Allergies      | ⬜        | Default: NKDA                |

**Never guess or fabricate clinical data.**

### Step 2 — Look Up ICD-10 Code

Read `references/icd10_common.md` to find the code for the diagnosis.
If not found, mark as: `[CODE PENDING — coding required]`

### Step 3 — Generate Report

Run the script:
```bash
python3 scripts/generate_report.py \
  --patient-name "John Doe" \
  --dob "1985-03-12" \
  --mrn "10042891" \
  --provider "Dr. Priya Sharma" \
  --complaint "Chest pain" \
  --vitals "BP:142/88,HR:94,Temp:37.1,SpO2:98,Weight:78" \
  --assessment "Angina pectoris | ICD-10: I20.9" \
  --plan "ECG stat; Troponin q6h; Aspirin 325mg"
```

### Step 4 — Validate Before Presenting

- [ ] All required fields present
- [ ] ICD-10 code included (or marked pending)
- [ ] HIPAA confidentiality header present
- [ ] No fabricated clinical data

### Step 5 — Present Output

Show report inline. Offer to save as `.txt`, `.docx`, or `.pdf`.

---

## Output Format

```
════════════════════════════════════════════════════════
    CLINICAL PATIENT REPORT  [FINAL/DRAFT]
    {facility}
    Generated : {date}
    Provider  : {provider}
    CONFIDENTIAL — HIPAA Protected Health Information
════════════════════════════════════════════════════════

PATIENT  : {name} | DOB: {dob} | MRN: {mrn}
ALLERGIES: {allergies}

── SUBJECTIVE ──────────────────────────────────────────
Chief Complaint : {complaint}
History (HPI)   : {hpi}
Past Med Hx     : {pmh}

── OBJECTIVE ────────────────────────────────────────────
  Blood Pressure : {bp} mmHg
  Heart Rate     : {hr} bpm
  Temperature    : {temp} °C
  SpO2           : {spo2}%
  Weight         : {weight} kg

── ASSESSMENT ───────────────────────────────────────────
Primary Dx : {icd10_code} — {diagnosis}
Secondary  : {secondary_dx}

── PLAN ─────────────────────────────────────────────────
  1. {plan item 1}
  2. {plan item 2}

── FOLLOW-UP ────────────────────────────────────────────
  Return Visit : {follow_up}
  Referring To : {referral}

════════════════════════════════════════════════════════
    END OF REPORT — {provider} | {date}
════════════════════════════════════════════════════════
```

---

## Compliance Rules

- Always include the HIPAA confidentiality header
- Never log or echo PHI outside the report document
- Mark incomplete reports as `DRAFT`
- Never invent clinical findings, medications, or history

---

## Reference Files

| File | Purpose | When to Read |
|------|---------|--------------|
| `references/icd10_common.md` | ICD-10 codes by body system | Every report |
| `assets/report_header.txt` | Header ASCII template | Optional reference |

