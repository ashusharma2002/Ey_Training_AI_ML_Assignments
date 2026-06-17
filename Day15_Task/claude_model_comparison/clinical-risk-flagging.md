# Claude Model Comparison — Clinical Note Risk Flagging

> **Prompt tested across three Claude models:**
> *"Summarise this patient note and flag any clinical or documentation risks: 'Pt c/o chest pain x2 days. Vitals stable. EKG done - unremarkable. Discharged home with ibuprofen and advised to follow up if symptoms worsen. No troponin ordered. Attending noted time pressure due to ED volume.'"*

---

## Table of Contents

- [Overview](#overview)
- [Model Responses](#model-responses)
  - [Claude Haiku 4.5](#1-claude-haiku-45)
  - [Claude Sonnet 4.6](#2-claude-sonnet-46)
  - [Claude Opus 4.8](#3-claude-opus-48)
- [Comparative Analysis](#comparative-analysis)
- [Verdict](#verdict)
- [Rephrased Prompt](#rephrased-prompt)

---

## Overview

This document captures the same clinical risk flagging prompt submitted to three Claude models — **Haiku 4.5**, **Sonnet 4.6**, and **Opus 4.8** — and evaluates their ability to identify clinical and medicolegal risks in a real patient note. The task requires balancing clinical knowledge with awareness of documentation and liability issues.

**Important note:** These responses are for risk assessment and educational purposes. Clinical and legal decisions require consultation with qualified physicians, risk managers, and legal counsel.

---

## Model Responses

### 1. Claude Haiku 4.5

**Response:**

Summary: Stable patient with 2 days of chest pain, normal EKG, discharged home on ibuprofen. Clinical risks: troponin was not ordered — this is a significant gap in evaluating acute coronary syndrome. With chest pain persisting for 2 days, serial troponins or a high-sensitivity troponin should have been considered, especially given the lack of a clear alternative diagnosis. Documentation risk: the note mentions time pressure due to ED volume, which while honest, documents a potential external pressure that influenced the clinical decision. This could be used in litigation to suggest the decision wasn't based purely on clinical judgment. Recommendation: order troponin before discharge, or if discharge is clinically appropriate, document the specific reasoning for omitting it and ensure close follow-up arrangements are made.

**Analysis:**

Haiku identifies the two main risks (missing troponin, time pressure documentation) and makes a practical recommendation. It correctly notes that mentioning time pressure in the medical record creates a liability issue. However, it lacks depth on the clinical reasoning behind troponin protocols and doesn't explore risk stratification frameworks.

**Strengths:**
- Identifies the critical missing test (troponin)
- Flags the documentation problem of mentioning time pressure
- Practical recommendation
- Direct and actionable

**Weaknesses:**
- Does not explain troponin protocols or why they're standard
- Misses the lack of documented differential diagnosis
- Does not mention vital sign specifics or risk factors needed for clinical triage
- Limited discussion of medicolegal exposure or standards of care
- Does not address the discharge instruction sufficiency
- Minimal exploration of follow-up inadequacy

---

### 2. Claude Sonnet 4.6

**Response:**

Summary: Patient with 2 days of chest pain, stable vitals, unremarkable EKG, discharged home with ibuprofen. Critical clinical gaps: (1) Troponin was not ordered — this is a significant omission. Chest pain with 2 days of duration requires rule-out of acute coronary syndrome (ACS), and troponin is the standard biomarker. An unremarkable EKG does not exclude ACS; troponin is essential to the evaluation. (2) No documented differential diagnosis — the note doesn't explain why alternative etiologies were ruled out or why discharge was safe. (3) Discharge instructions are minimal; "follow up if symptoms worsen" is insufficient for a chest pain patient, who may not recognize worsening or may delay seeking care. Documentation risks: The explicit mention of time pressure is problematic. In a legal review, this language suggests the clinical decision was influenced by external operational factors rather than pure clinical judgment, and plaintiffs' counsel would argue the physician was rushed. The note also lacks risk stratification — there's no documented assessment of chest pain characteristics (quality, radiation, associated symptoms), cardiac risk factors, or why the patient was deemed low-risk enough to discharge. Recommendation: Before discharge, either obtain troponin (and ideally serial or high-sensitivity troponin) or explicitly document the clinical reasoning for omission, along with a detailed assessment of risk factors and differential diagnosis. Provide specific discharge instructions (when to call 911, when to return to ED) and ensure documented close follow-up.

**Analysis:**

Sonnet provides comprehensive risk identification with clinical and medicolegal depth. It explains *why* troponin matters (standard for ACS rule-out), identifies missing documentation elements, and explains the specific liability risk of mentioning time pressure. It frames the issue as missing documentation of clinical reasoning, not just missing tests.

**Strengths:**
- Explains the clinical standard (troponin for ACS rule-out)
- Identifies missing differential diagnosis documentation
- Flags inadequate discharge instructions
- Clearly explains the liability risk of time pressure mention
- Addresses risk stratification gaps
- More sophisticated medicolegal framing
- Practical, specific recommendations

**Weaknesses:**
- Does not quantify the legal/regulatory exposure
- Doesn't mention specific risk scores (HEART, TIMI) that should guide the note
- Could have addressed documentation of patient education
- Misses potential systemic issues (why was troponin not part of protocol?)

---

### 3. Claude Opus 4.8

**Response:**

Summary: 2-day chest pain patient with stable vitals, unremarkable EKG, discharged home on ibuprofen with "follow up if worse" instructions. This note has multiple clinical, documentation, and medicolegal exposures that require immediate attention.

**Critical clinical gaps:**

1. **Troponin omission is the highest-risk item.** Standard of care for chest pain evaluation includes troponin to rule out acute coronary syndrome (ACS), regardless of EKG findings. High-sensitivity troponin (if available) should be considered for patients presenting within hours of symptom onset; conventional troponin has time-dependent sensitivity. The note provides no explanation for why troponin was omitted — no documentation of clinical reasoning, risk stratification, or decision-making process. This silence is itself a liability: if the patient has a subsequent MI, the absence of documented reasoning for the troponin omission will be a focal point in litigation.

2. **No documented risk stratification.** The note lacks any assessment of chest pain characteristics (quality, duration, radiation, associated dyspnea, diaphoresis, nausea), cardiac risk factors (age, smoking, diabetes, family history, prior CAD), or application of a validated risk tool (HEART score, TIMI, ACS risk calculator). Without this, it's impossible to verify the clinical reasoning for discharge. A court would view the lack of risk stratification as evidence the assessment was incomplete.

3. **Absent differential diagnosis.** The note doesn't document consideration of alternative etiologies (musculoskeletal, GI, pulmonary, anxiety) or explain why they were ruled out. This is necessary to justify the low-risk discharge decision.

4. **Inadequate discharge instructions.** "Follow up if symptoms worsen" is vague and potentially dangerous. For chest pain, discharge instructions must specify: call 911 if chest pain recurs or worsens, return to ED for any new symptoms (dyspnea, diaphoresis, palpitations), follow up with primary care within 24-48 hours, avoid strenuous activity. There is no documentation that patient education occurred.

**Documentation and medicolegal risks:**

1. **Time pressure documentation is severely problematic.** Documenting "time pressure due to ED volume" in the medical record is nearly indefensible in litigation. It explicitly attributes the clinical decision to an operational constraint rather than clinical judgment. A plaintiff attorney will argue: "The note shows the attending felt pressured and discharged this patient without appropriate workup." This single sentence undermines the credibility of the entire clinical decision. **This must be removed or reframed** — if there were legitimate clinical reasons for discharge, document those instead. If the decision was influenced by volume, that's an institutional problem requiring escalation, not documentation in the chart.

2. **Missing informed consent documentation.** There's no evidence the patient was informed of the risk of missed ACS, the limitations of the evaluation, or the importance of follow-up. Modern practice requires documented shared decision-making for discharge of a patient with unresolved chest pain.

3. **Incomplete vital signs.** "Vitals stable" is not sufficiently specific. The note should document BP, HR, RR, O2 sat, and temperature — essential data for risk assessment.

4. **Standards of care concern.** Many EDs have ACS protocols requiring troponin for all chest pain presentations, particularly if symptoms persist. The note suggests no protocol compliance check or documentation of deviation rationale.

**Systemic and institutional risks:**

- If the ED frequently discharges chest pain patients without troponin due to volume pressure, there is a systemic quality and safety issue requiring escalation to medical leadership.
- The documentation of time pressure suggests institutional awareness of this practice, which increases liability exposure.

**Liability exposure:** This case has a moderately high malpractice risk profile. If the patient has a subsequent MI within days, a plaintiff would argue: (1) the troponin omission fell below standard of care, (2) the EKG alone is insufficient for ACS rule-out, (3) the time pressure documentation proves clinical judgment was compromised, and (4) inadequate risk stratification and discharge instructions prevented appropriate patient follow-up. The defense would struggle given the documentation gaps.

**Immediate actions:**

1. **Chart correction:** Remove or reframe the time pressure statement. Replace with specific clinical reasoning: "Risk stratified as low-risk via [tool used], differential diagnosis considered, patient counseled on warning signs and close follow-up."
2. **If patient still in follow-up window:** Obtain troponin retroactively or escalate to cardiology for risk assessment.
3. **If patient not yet followed up:** Contact for urgent outpatient evaluation and troponin if not performed.
4. **Institutional:** If this is a pattern, escalate to quality/risk management. Volume-driven discharge decisions are a systemic issue, not an individual charting problem.
5. **Education:** Ensure attending is aware of institutional ACS protocols and the medicolegal risks of inadequate documentation.

**Documentation template for future chest pain cases (example):**

"Patient presents with [specifics of pain]. Risk stratification via HEART score: [score] (low/intermediate/high). Differential diagnosis considered: ACS (ruled out via EKG and troponin), musculoskeletal (unlikely due to [findings]), GI (unlikely due to [findings]). Plan: discharge with [specific instructions], follow up with PCP in [timeframe], return precautions provided. Patient education: explained ACS risk, importance of follow-up, warning signs."

---

**Analysis:**

Opus provides the most comprehensive risk assessment. It not only identifies the missing test and documentation problems but explains the clinical *why*, explores the medicolegal pathway (how a plaintiff would argue the case), and identifies systemic issues. It distinguishes between missing data and missing reasoning, which is critical in medical malpractice defense.

**Strengths:**
- Explains clinical standards and why they matter (ACS rule-out)
- Identifies specific gaps in risk stratification and differential diagnosis
- Clearly articulates the liability path (what a plaintiff would argue)
- Flags time pressure documentation as "nearly indefensible"
- Addresses systemic/institutional risk, not just individual case
- Provides actionable remediation steps
- Includes a documentation template for future cases
- Distinguishes between "missing troponin" and "missing *reasoning* for omitting troponin"
- Addresses patient education and informed consent
- Most useful for risk management and quality improvement

**Weaknesses:**
- Very long response; may be overwhelming for a front-line physician
- Some assumptions about institutional protocols not specified in the note
- Does not address specific troponin assay choices (conventional vs. high-sensitivity timing)

---

## Comparative Analysis

| Criterion | Haiku 4.5 | Sonnet 4.6 | Opus 4.8 |
|---|---|---|---|
| **Identifies troponin omission** | ✅ Yes | ✅ Yes | ✅ Yes, with detail |
| **Explains clinical standard** | ⚠️ Brief | ✅ Clear | ✅ Comprehensive |
| **Flags time pressure liability** | ✅ Yes | ✅ Yes, strong | ✅ Yes, "nearly indefensible" |
| **Identifies missing risk stratification** | ❌ No | ✅ Yes | ✅ Yes, specific |
| **Identifies missing differential diagnosis** | ❌ No | ✅ Yes | ✅ Yes, detailed |
| **Addresses inadequate discharge instructions** | ❌ No | ✅ Yes | ✅ Yes, with examples |
| **Flags informed consent gap** | ❌ No | ❌ No | ✅ Yes |
| **Addresses systemic/institutional risk** | ❌ No | ❌ No | ✅ Yes |
| **Provides remediation steps** | ⚠️ General | ✅ Specific | ✅ Detailed & actionable |
| **Liability exposure quantification** | ❌ None | ❌ None | ✅ "Moderately high" |
| **Documentation template** | ❌ No | ❌ No | ✅ Yes |
| **Appropriate for front-line use** | ✅ Yes | ✅ Yes | ⚠️ Detailed |
| **Appropriate for risk review** | ⚠️ Incomplete | ✅ Good | ✅ Excellent |

---

## Verdict

### 🏆 Best overall response: **Claude Opus 4.8**

For clinical risk flagging and medicolegal assessment, **Opus is the gold standard.** It identifies not only *what* is missing but *why* it matters clinically and legally, and it explains how those gaps would be weaponized in a malpractice suit. Critically, Opus distinguishes between a missing troponin and the *absence of documented reasoning* for the omission — the latter is the liability driver.

However, the appropriate model depends on the use case:

**When to use each model:**

| Use case | Recommended model |
|---|---|
| Front-line clinician needing quick risk check | **Sonnet 4.6** |
| Quality/risk manager reviewing cases | **Opus 4.8** |
| Rapid triage for high-volume ED screening | **Haiku 4.5** |

---

## Model Performance Summary

**Haiku 4.5:** Identifies the headline risk (missing troponin) but lacks the depth to understand the full exposure. Suitable for rapid flagging but not for detailed risk review. A busy attending might use this as a quick checklist, but it's insufficient for a risk management review.

**Sonnet 4.6:** Best balance of clinical depth and actionability. Identifies the key documentation gaps (missing differential, inadequate discharge instructions), explains the medicolegal risk clearly, and provides specific recommendations. Strong choice for a clinician or quality reviewer who needs to understand the case quickly and act.

**Opus 4.8:** Most comprehensive. Provides the clinical, documentation, and institutional perspective. Essential for malpractice defense preparation, root cause analysis, or policy development. Overkill for a single case review but invaluable for systemic assessment.

---

## Clinical Context & Standards

For reference, the following are standard of care considerations in chest pain evaluation:

**ACS rule-out requires:**
- Serial or high-sensitivity troponin (time-dependent; 0-3 hours from symptom onset for conventional troponin)
- EKG (necessary but not sufficient; 5% of ACS presents with normal EKG)
- Clinical risk stratification (age, risk factors, symptom characteristics)
- Validated risk tool (HEART, TIMI, ACS Risk Calculator)

**Inadequate documentation of any of these creates liability exposure.**

---

## Rephrased Prompt

The original prompt is vague and lacks clinical context. Below is a structured version optimised for clearer, more consistent output:

---

**Rephrased prompt:**

> You are a clinical risk manager. Review this patient note for clinical and documentation risks:
>
> **Clinical presentation:**
> - Chief complaint: chest pain x 2 days
> - Vital signs: documented as "stable" (specific values not recorded)
> - Physical examination findings: not documented
> - EKG: performed, reported as "unremarkable"
>
> **Workup:**
> - Troponin: not ordered
> - Other cardiac biomarkers: not documented
> - Imaging: not documented
> - Risk stratification: not documented
> - Differential diagnosis documentation: not documented
>
> **Disposition:**
> - Discharge to home with ibuprofen
> - Discharge instructions: "follow up if symptoms worsen"
> - Follow-up plan: not documented
>
> **Additional context:**
> - Note explicitly documents "time pressure due to ED volume" as a contextual factor
> - Patient has no prior records or cardiac history documented
>
> **Your task:**
> 1. Summarise the clinical presentation and workup.
> 2. Identify any clinical gaps that fall below standard of care.
> 3. Identify any documentation risks that increase liability exposure.
> 4. Explain how each gap would be used in a malpractice lawsuit.
> 5. Recommend specific corrective actions (charting, patient follow-up, or institutional).
> 6. Rate the overall liability exposure (low / moderate / high).

---

**Why this version is better:**

- Separates presentation, workup, and disposition clearly
- Explicitly asks for gaps vs. standard of care
- Asks for medicolegal pathway (how would plaintiff use this?)
- Requests actionable remediation
- Asks for liability quantification
- Produces more structured, comparable responses

---

## Conclusion

All three models identified the missing troponin as a critical gap. The differences lie in depth and context:

- **Haiku** flags the headline risk but misses the supporting documentation architecture.
- **Sonnet** identifies the full set of documentation gaps and explains the liability clearly.
- **Opus** goes further — it explains the plaintiff's litigation strategy, identifies systemic issues, and provides remediation and prevention strategies.

**For clinical risk flagging, Opus is the best model.** The cost of incomplete risk assessment in medicine is patient harm and malpractice exposure, both of which demand the most thorough analysis available. Sonnet is a strong second choice for busy clinicians who need depth without the length.

The most important takeaway: **documenting time pressure in the medical record is nearly indefensible and should never appear in the chart.** If clinical decisions are being influenced by volume, that's a systemic problem requiring escalation to medical leadership, not documentation in the patient's note.

---

*Generated using Claude model comparison methodology · Responses captured from identical prompt across Haiku 4.5, Sonnet 4.6, and Opus 4.8 · For clinical risk assessment and educational purposes · Not a substitute for medical or legal consultation*

**Disclaimer:** These responses are for educational and risk assessment purposes. Clinical and legal decisions require consultation with qualified physicians, risk managers, patient safety officers, and legal counsel.
