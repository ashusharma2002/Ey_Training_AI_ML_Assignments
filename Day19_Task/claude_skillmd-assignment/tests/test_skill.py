#!/usr/bin/env python3
"""
test_skill.py — Unit tests for generate_report.py

Run:
    python3 tests/test_skill.py
"""

import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../skill/scripts"))
from generate_report import generate_report, parse_vitals, validate, numbered_list

BASE = {
    "patient_name": "Test Patient",
    "dob":          "1990-01-01",
    "mrn":          "TEST-001",
    "provider":     "Dr. Test",
    "complaint":    "Fever",
    "vitals":       "BP:120/80,HR:72,Temp:38.5,SpO2:98,Weight:65",
    "assessment":   "Viral fever | ICD-10: B34.9",
    "plan":         "Rest; Paracetamol 500mg; Fluids",
    "facility":     "Test Hospital",
}


class TestParseVitals(unittest.TestCase):
    def test_all_fields(self):
        v = parse_vitals("BP:120/80,HR:72,Temp:38.5,SpO2:98,Weight:65")
        self.assertEqual(v["BP"], "120/80")
        self.assertEqual(v["HR"], "72")
        self.assertEqual(v["TEMP"], "38.5")

    def test_empty(self):
        self.assertEqual(parse_vitals(""), {})

    def test_partial(self):
        v = parse_vitals("BP:130/85,HR:80")
        self.assertIn("BP", v)
        self.assertNotIn("TEMP", v)


class TestValidate(unittest.TestCase):
    def test_valid_returns_empty(self):
        self.assertEqual(validate(BASE), [])

    def test_missing_name(self):
        self.assertIn("patient_name", validate({**BASE, "patient_name": ""}))

    def test_missing_multiple(self):
        missing = validate({**BASE, "mrn": "", "plan": ""})
        self.assertIn("mrn", missing)
        self.assertIn("plan", missing)


class TestNumberedList(unittest.TestCase):
    def test_three_items(self):
        r = numbered_list("Rest; Fluids; Paracetamol")
        self.assertIn("1.", r)
        self.assertIn("2.", r)
        self.assertIn("3.", r)

    def test_single(self):
        self.assertIn("1.", numbered_list("ECG stat"))

    def test_strips_spaces(self):
        r = numbered_list("  Rest  ;  Fluids  ")
        self.assertIn("Rest", r)


class TestGenerateReport(unittest.TestCase):
    def test_generates_report(self):
        r = generate_report(BASE)
        self.assertIn("CLINICAL PATIENT REPORT", r)
        self.assertIn("Test Patient", r)
        self.assertIn("HIPAA", r)

    def test_all_sections_present(self):
        r = generate_report(BASE)
        for section in ["SUBJECTIVE", "OBJECTIVE", "ASSESSMENT", "PLAN"]:
            self.assertIn(section, r)

    def test_raises_on_missing(self):
        with self.assertRaises(ValueError):
            generate_report({"patient_name": "X"})

    def test_draft_flag(self):
        self.assertIn("DRAFT", generate_report({**BASE, "draft": True}))

    def test_final_default(self):
        self.assertIn("FINAL", generate_report(BASE))

    def test_icd10_in_output(self):
        self.assertIn("B34.9", generate_report(BASE))

    def test_default_allergy(self):
        data = {k: v for k, v in BASE.items() if k != "allergies"}
        self.assertIn("NKDA", generate_report(data))

    def test_custom_allergy(self):
        self.assertIn("Penicillin", generate_report({**BASE, "allergies": "Penicillin (rash)"}))

    def test_vitals_in_output(self):
        r = generate_report(BASE)
        self.assertIn("120/80", r)
        self.assertIn("38.5", r)

    def test_plan_numbered(self):
        r = generate_report(BASE)
        self.assertIn("1.", r)
        self.assertIn("2.", r)

    def test_hipaa_header(self):
        self.assertIn("CONFIDENTIAL", generate_report(BASE))


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.TestLoader().loadTestsFromModule(
        sys.modules[__name__]
    ))
    sys.exit(0 if result.wasSuccessful() else 1)
