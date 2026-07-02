# scripts/generate_test_profiles.py
# ============================================================
# Phase 3 — Test Dataset Generation.
# Generates 4 fictional customer profiles as realistic PDF
# documents you can upload directly into the app to test every
# workflow (customer loan, institution review, retirement, etc.)
#
# ALL DATA IS 100% FICTIONAL. Names, numbers, IDs are made up for
# testing purposes only and do not represent real people.
#
# HOW TO RUN:
#   python scripts/generate_test_profiles.py
#
# Output: data/test_profiles/<profile_name>/*.pdf
# ============================================================
from __future__ import annotations
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUTPUT_DIR = Path("data/test_profiles")
styles = getSampleStyleSheet()

title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
heading_style = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], fontSize=12, spaceAfter=8, textColor=colors.HexColor("#1F2937"))
body_style = styles["Normal"]
disclaimer_style = ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=8, textColor=colors.grey)


def _make_pdf(filepath: Path, title: str, sections: list[tuple[str, list]]) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(filepath), pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm,
                             leftMargin=2*cm, rightMargin=2*cm)
    elements = [
        Paragraph(title, title_style),
        Paragraph(
            "NOTE — FICTIONAL TEST DOCUMENT: All names, numbers, and IDs on this page "
            "are entirely made up for software testing purposes only.",
            disclaimer_style,
        ),
        Spacer(1, 0.5*cm),
    ]
    for heading, rows in sections:
        elements.append(Paragraph(heading, heading_style))
        if isinstance(rows, list) and rows and isinstance(rows[0], (list, tuple)):
            table = Table(rows, colWidths=[7*cm, 7*cm])
            table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph(str(rows), body_style))
        elements.append(Spacer(1, 0.4*cm))
    doc.build(elements)
    print(f"  ✅ {filepath}")


# ════════════════════════════════════════════════════════════
# PROFILE 1 — Young Salaried Employee
# ════════════════════════════════════════════════════════════
def profile_young_salaried():
    base = OUTPUT_DIR / "01_young_salaried_employee"
    print("Generating: Young Salaried Employee (Rohan Mehta, 26)")

    _make_pdf(base / "salary_slip.pdf", "Salary Slip — March 2026", [
        ("Employee Details", [
            ["Name", "Rohan Mehta"], ["Employee ID", "TST-EMP-1001"],
            ["Designation", "Software Engineer I"], ["Department", "Engineering"],
            ["Date of Joining", "15 June 2023"], ["Date of Birth", "12 Aug 1999"],
        ]),
        ("Earnings", [
            ["Basic Salary", "Rs. 38,000"], ["HRA", "Rs. 15,200"],
            ["Special Allowance", "Rs. 12,800"], ["Gross Salary", "Rs. 66,000"],
        ]),
        ("Deductions", [
            ["Provident Fund", "Rs. 4,560"], ["Professional Tax", "Rs. 200"],
            ["Income Tax (TDS)", "Rs. 2,100"], ["Net Salary (Take Home)", "Rs. 59,140"],
        ]),
    ])

    _make_pdf(base / "bank_statement.pdf", "Bank Statement Summary — Q1 2026", [
        ("Account Summary", [
            ["Account Holder", "Rohan Mehta"], ["Account Type", "Savings"],
            ["Average Monthly Balance", "Rs. 85,000"], ["Opening Balance (Jan)", "Rs. 62,000"],
            ["Closing Balance (Mar)", "Rs. 91,500"],
        ]),
        ("Monthly Cash Flow", [
            ["Avg. Monthly Credit (Salary)", "Rs. 59,140"],
            ["Avg. Monthly Debit (Rent)", "Rs. 15,000"],
            ["Avg. Monthly Debit (Other expenses)", "Rs. 22,000"],
            ["Avg. Monthly Savings", "Rs. 22,140"],
        ]),
    ])

    _make_pdf(base / "credit_score_report.pdf", "Credit Score Report", [
        ("Credit Summary", [
            ["Credit Score (CIBIL)", "742"], ["Score Band", "Good"],
            ["Total Active Accounts", "2"], ["Credit Card Utilisation", "28%"],
            ["Payment History", "100% on-time (last 24 months)"],
            ["Existing Loans", "1 — Personal Loan, Rs. 1,20,000 outstanding"],
        ]),
    ])

    _make_pdf(base / "itr_summary.pdf", "Income Tax Return Summary — AY 2025-26", [
        ("ITR Details", [
            ["PAN", "TSTPA1234X"], ["Assessment Year", "2025-26"],
            ["Gross Total Income", "Rs. 7,92,000"], ["Tax Paid", "Rs. 48,600"],
            ["Filing Status", "Filed on time"],
        ]),
    ])
    print()


# ════════════════════════════════════════════════════════════
# PROFILE 2 — Mid-Career Professional
# ════════════════════════════════════════════════════════════
def profile_mid_career():
    base = OUTPUT_DIR / "02_mid_career_professional"
    print("Generating: Mid-Career Professional (Priya Nair, 38)")

    _make_pdf(base / "salary_slip.pdf", "Salary Slip — March 2026", [
        ("Employee Details", [
            ["Name", "Priya Nair"], ["Employee ID", "TST-EMP-2002"],
            ["Designation", "Senior Manager — Finance"], ["Department", "Finance"],
            ["Date of Joining", "3 April 2016"], ["Date of Birth", "21 Feb 1988"],
        ]),
        ("Earnings", [
            ["Basic Salary", "Rs. 95,000"], ["HRA", "Rs. 38,000"],
            ["Special Allowance", "Rs. 42,000"], ["Performance Bonus (Monthly avg.)", "Rs. 15,000"],
            ["Gross Salary", "Rs. 1,90,000"],
        ]),
        ("Deductions", [
            ["Provident Fund", "Rs. 11,400"], ["Professional Tax", "Rs. 200"],
            ["Income Tax (TDS)", "Rs. 28,500"], ["Net Salary (Take Home)", "Rs. 1,49,900"],
        ]),
    ])

    _make_pdf(base / "bank_statement.pdf", "Bank Statement Summary — Q1 2026", [
        ("Account Summary", [
            ["Account Holder", "Priya Nair"], ["Account Type", "Savings"],
            ["Average Monthly Balance", "Rs. 4,20,000"],
            ["Opening Balance (Jan)", "Rs. 3,80,000"], ["Closing Balance (Mar)", "Rs. 4,65,000"],
        ]),
        ("Monthly Cash Flow", [
            ["Avg. Monthly Credit (Salary)", "Rs. 1,49,900"],
            ["Avg. Monthly Debit (Home Loan EMI)", "Rs. 42,000"],
            ["Avg. Monthly Debit (Other expenses)", "Rs. 58,000"],
            ["Avg. Monthly Savings", "Rs. 49,900"],
        ]),
    ])

    _make_pdf(base / "credit_score_report.pdf", "Credit Score Report", [
        ("Credit Summary", [
            ["Credit Score (CIBIL)", "801"], ["Score Band", "Excellent"],
            ["Total Active Accounts", "3"], ["Credit Card Utilisation", "15%"],
            ["Payment History", "100% on-time (last 36 months)"],
            ["Existing Loans", "1 — Home Loan, Rs. 38,50,000 outstanding (Tenure: 14 yrs remaining)"],
        ]),
    ])

    _make_pdf(base / "existing_loan_statement.pdf", "Existing Loan Statement — Home Loan", [
        ("Loan Details", [
            ["Lender", "Test Bank Ltd."], ["Loan Type", "Home Loan"],
            ["Original Amount", "Rs. 52,00,000"], ["Outstanding Balance", "Rs. 38,50,000"],
            ["Monthly EMI", "Rs. 42,000"], ["Interest Rate", "8.65% p.a."],
            ["Tenure Remaining", "14 years"], ["Repayment History", "No defaults"],
        ]),
    ])
    print()


# ════════════════════════════════════════════════════════════
# PROFILE 3 — Small Business Owner
# ════════════════════════════════════════════════════════════
def profile_small_business():
    base = OUTPUT_DIR / "03_small_business_owner"
    print("Generating: Small Business Owner (Arjun Patel, 45)")

    _make_pdf(base / "business_income_statement.pdf", "Business Income Statement — FY 2025-26", [
        ("Business Details", [
            ["Proprietor", "Arjun Patel"], ["Business Name", "Patel Hardware & Tools"],
            ["Business Type", "Sole Proprietorship — Retail"],
            ["GST Registration", "TSTGST29ABCDE1Z2"], ["Years in Operation", "9 years"],
        ]),
        ("Income & Expenses", [
            ["Annual Revenue", "Rs. 68,00,000"], ["Cost of Goods Sold", "Rs. 44,20,000"],
            ["Operating Expenses", "Rs. 12,80,000"], ["Net Profit", "Rs. 11,00,000"],
            ["Net Profit Margin", "16.2%"],
        ]),
    ])

    _make_pdf(base / "gst_summary.pdf", "GST Filing Summary — FY 2025-26", [
        ("GST Summary", [
            ["GSTIN", "TSTGST29ABCDE1Z2"], ["Filing Frequency", "Monthly"],
            ["Total Outward Supply (Annual)", "Rs. 68,00,000"],
            ["Total Tax Paid (Annual)", "Rs. 6,12,000"],
            ["Filing Compliance", "All returns filed on time — last 12 months"],
        ]),
    ])

    _make_pdf(base / "bank_statement.pdf", "Current Account Statement Summary — Q1 2026", [
        ("Account Summary", [
            ["Account Holder", "Patel Hardware & Tools"], ["Account Type", "Current Account"],
            ["Average Monthly Balance", "Rs. 2,10,000"],
            ["Opening Balance (Jan)", "Rs. 1,85,000"], ["Closing Balance (Mar)", "Rs. 2,40,000"],
        ]),
        ("Monthly Cash Flow", [
            ["Avg. Monthly Inflow (Sales)", "Rs. 5,66,000"],
            ["Avg. Monthly Outflow (Purchases + Expenses)", "Rs. 4,75,000"],
            ["Avg. Monthly Net Cash Flow", "Rs. 91,000"],
        ]),
    ])

    _make_pdf(base / "credit_score_report.pdf", "Credit Score Report", [
        ("Credit Summary", [
            ["Credit Score (CIBIL)", "695"], ["Score Band", "Fair"],
            ["Total Active Accounts", "3"], ["Credit Card Utilisation", "55%"],
            ["Payment History", "2 late payments in last 12 months"],
            ["Existing Loans", "1 — Business Loan, Rs. 8,00,000 outstanding"],
        ]),
    ])

    _make_pdf(base / "existing_loan_statement.pdf", "Existing Loan Statement — Business Loan", [
        ("Loan Details", [
            ["Lender", "Test NBFC Pvt. Ltd."], ["Loan Type", "Business Loan"],
            ["Original Amount", "Rs. 12,00,000"], ["Outstanding Balance", "Rs. 8,00,000"],
            ["Monthly EMI", "Rs. 45,000"], ["Interest Rate", "14.5% p.a."],
            ["Tenure Remaining", "20 months"], ["Repayment History", "2 delayed payments (within 15 days)"],
        ]),
    ])
    print()


# ════════════════════════════════════════════════════════════
# PROFILE 4 — High-Income Customer
# ════════════════════════════════════════════════════════════
def profile_high_income():
    base = OUTPUT_DIR / "04_high_income_customer"
    print("Generating: High-Income Customer (Dr. Kavita Iyer, 52)")

    _make_pdf(base / "salary_slip.pdf", "Salary Slip — March 2026", [
        ("Employee Details", [
            ["Name", "Dr. Kavita Iyer"], ["Employee ID", "TST-EMP-4004"],
            ["Designation", "Chief Medical Officer"], ["Department", "Hospital Administration"],
            ["Date of Joining", "1 July 2010"], ["Date of Birth", "5 May 1974"],
        ]),
        ("Earnings", [
            ["Basic Salary", "Rs. 2,80,000"], ["HRA", "Rs. 1,12,000"],
            ["Special Allowance", "Rs. 95,000"], ["Consulting Fees (Monthly avg.)", "Rs. 1,50,000"],
            ["Gross Monthly Income", "Rs. 6,37,000"],
        ]),
        ("Deductions", [
            ["Provident Fund", "Rs. 33,600"], ["Professional Tax", "Rs. 200"],
            ["Income Tax (TDS)", "Rs. 1,85,000"], ["Net Monthly Income (Take Home)", "Rs. 4,18,200"],
        ]),
    ])

    _make_pdf(base / "bank_statement.pdf", "Bank Statement Summary — Q1 2026", [
        ("Account Summary", [
            ["Account Holder", "Dr. Kavita Iyer"], ["Account Type", "Savings (Premium)"],
            ["Average Monthly Balance", "Rs. 18,50,000"],
            ["Opening Balance (Jan)", "Rs. 16,20,000"], ["Closing Balance (Mar)", "Rs. 21,40,000"],
        ]),
        ("Monthly Cash Flow", [
            ["Avg. Monthly Credit (Salary + Consulting)", "Rs. 4,18,200"],
            ["Avg. Monthly Debit (Existing Home Loan EMI)", "Rs. 95,000"],
            ["Avg. Monthly Debit (Other expenses)", "Rs. 1,20,000"],
            ["Avg. Monthly Savings", "Rs. 2,03,200"],
        ]),
    ])

    _make_pdf(base / "credit_score_report.pdf", "Credit Score Report", [
        ("Credit Summary", [
            ["Credit Score (CIBIL)", "835"], ["Score Band", "Excellent"],
            ["Total Active Accounts", "5"], ["Credit Card Utilisation", "8%"],
            ["Payment History", "100% on-time (last 60 months)"],
            ["Existing Loans", "1 — Home Loan, Rs. 65,00,000 outstanding"],
        ]),
    ])

    _make_pdf(base / "investment_portfolio.pdf", "Investment Portfolio Summary", [
        ("Investment Holdings", [
            ["Mutual Funds (Equity)", "Rs. 85,00,000"], ["Fixed Deposits", "Rs. 40,00,000"],
            ["PPF Balance", "Rs. 18,50,000"], ["Stocks (Direct Equity)", "Rs. 32,00,000"],
            ["Total Investment Value", "Rs. 1,75,50,000"],
        ]),
    ])

    _make_pdf(base / "existing_loan_statement.pdf", "Existing Loan Statement — Home Loan", [
        ("Loan Details", [
            ["Lender", "Test Bank Ltd."], ["Loan Type", "Home Loan"],
            ["Original Amount", "Rs. 90,00,000"], ["Outstanding Balance", "Rs. 65,00,000"],
            ["Monthly EMI", "Rs. 95,000"], ["Interest Rate", "8.40% p.a."],
            ["Tenure Remaining", "9 years"], ["Repayment History", "No defaults"],
        ]),
    ])
    print()


def profile_bad_credit_individual():
    """
    Profile 5 — Bad Credit Individual (Deepak Sharma, 34)

    WHY BANK WILL REJECT:
    - CIBIL score 511 (anything below 650 is high-risk for most banks)
    - 3 existing EMIs eating 78% of net salary — extreme DTI ratio
    - 2 loan defaults in the past 12 months
    - Credit card utilisation 91% (above 30% is a red flag)
    - Irregular bank deposits suggesting unstable income
    - Asked for Rs. 8,00,000 personal loan on a Rs. 28,000 net salary
    - No savings/investments — zero buffer against default
    """
    base = OUTPUT_DIR / "05_bad_credit_individual"
    print("Generating: BAD PROFILE — Deepak Sharma, 34 (High-risk individual, bank rejection expected)")

    _make_pdf(base / "salary_slip.pdf", "Salary Slip — March 2026", [
        ("Employee Details", [
            ["Name", "Deepak Sharma"], ["Employee ID", "TST-EMP-5001"],
            ["Designation", "Data Entry Operator"], ["Department", "Operations"],
            ["Date of Joining", "14 January 2022"], ["Date of Birth", "9 March 1992"],
        ]),
        ("Earnings", [
            ["Basic Salary", "Rs. 18,000"], ["HRA", "Rs. 5,400"],
            ["Special Allowance", "Rs. 4,600"], ["Gross Salary", "Rs. 28,000"],
        ]),
        ("Deductions", [
            ["Provident Fund", "Rs. 2,160"], ["Professional Tax", "Rs. 200"],
            ["Income Tax (TDS)", "Rs. 0 (income below taxable limit)"],
            ["Net Salary (Take Home)", "Rs. 25,640"],
        ]),
        ("Employment Notes", [
            ["Contract Type", "Fixed-term contract (renewed annually)"],
            ["Employment Stability", "Third employer in 4 years"],
        ]),
    ])

    _make_pdf(base / "bank_statement.pdf", "Bank Statement Summary — Q1 2026", [
        ("Account Summary", [
            ["Account Holder", "Deepak Sharma"], ["Account Type", "Savings"],
            ["Average Monthly Balance", "Rs. 2,100 (frequently dips below Rs. 500)"],
            ["Opening Balance (Jan)", "Rs. 3,200"],
            ["Closing Balance (Mar)", "Rs. 890"],
        ]),
        ("Monthly Cash Flow", [
            ["Avg. Monthly Credit (Salary)", "Rs. 25,640"],
            ["Avg. Monthly Debit (EMI — Personal Loan 1)", "Rs. 8,500"],
            ["Avg. Monthly Debit (EMI — Two-Wheeler Loan)", "Rs. 4,200"],
            ["Avg. Monthly Debit (EMI — Consumer Durable Loan)", "Rs. 3,300"],
            ["Avg. Monthly Debit (Rent)", "Rs. 6,500"],
            ["Avg. Monthly Debit (Other expenses)", "Rs. 5,000"],
            ["Net Monthly Surplus", "Rs. -1,860 (negative — spending exceeds income)"],
        ]),
        ("Irregularities Noted", [
            ["Bounced ECS/NACH mandates (last 3 months)", "3 instances"],
            ["Minimum balance penalty charges", "Rs. 590 (2 months)"],
            ["Salary credited late (Jan 2026)", "Credited on 8th instead of 1st"],
        ]),
    ])

    _make_pdf(base / "credit_score_report.pdf", "Credit Score Report", [
        ("Credit Summary", [
            ["Credit Score (CIBIL)", "511"],
            ["Score Band", "Poor — High Risk"],
            ["Total Active Accounts", "5"],
            ["Credit Card Utilisation", "91% (Rs. 91,000 of Rs. 1,00,000 limit used)"],
            ["Payment History", "2 defaults in last 12 months; 5 late payments in 24 months"],
            ["Loan 1 — Personal Loan", "Rs. 1,80,000 outstanding; 2 EMIs overdue"],
            ["Loan 2 — Two-Wheeler Loan", "Rs. 68,000 outstanding; 1 EMI overdue"],
            ["Loan 3 — Consumer Durable", "Rs. 42,000 outstanding; current"],
            ["Credit Card", "Rs. 91,000 outstanding; minimum payment only last 6 months"],
            ["Written-off Account", "1 account written off in 2023 (Rs. 35,000)"],
        ]),
        ("Risk Indicators", [
            ["Debt-to-Income Ratio", "Approx. 78% (critical threshold is 50%)"],
            ["Number of Hard Enquiries (6 months)", "7 (multiple recent loan applications)"],
            ["Recommendation", "DECLINE — significant default risk"],
        ]),
    ])

    _make_pdf(base / "existing_loan_statement.pdf", "Existing Loan Statements — Combined", [
        ("Loan 1 — Personal Loan (Overdue)", [
            ["Lender", "Test NBFC Pvt. Ltd."], ["Original Amount", "Rs. 3,00,000"],
            ["Outstanding Balance", "Rs. 1,80,000"], ["Monthly EMI", "Rs. 8,500"],
            ["Interest Rate", "22% p.a. (high-risk borrower rate)"],
            ["Repayment Status", "OVERDUE — 2 EMIs missed (Jan & Feb 2026)"],
            ["Days Past Due", "62 days"],
        ]),
        ("Loan 2 — Two-Wheeler Loan (Overdue)", [
            ["Lender", "Test Finance Ltd."], ["Original Amount", "Rs. 95,000"],
            ["Outstanding Balance", "Rs. 68,000"], ["Monthly EMI", "Rs. 4,200"],
            ["Interest Rate", "18% p.a."],
            ["Repayment Status", "OVERDUE — 1 EMI missed (Feb 2026)"],
            ["Days Past Due", "28 days"],
        ]),
        ("Loan 3 — Consumer Durable", [
            ["Lender", "Test Bank Ltd."], ["Original Amount", "Rs. 55,000"],
            ["Outstanding Balance", "Rs. 42,000"], ["Monthly EMI", "Rs. 3,300"],
            ["Repayment Status", "Current — but minimum payments only"],
        ]),
    ])
    print()


def profile_bad_credit_business():
    """
    Profile 6 — Struggling Small Business (Meena Pillai, 41)

    WHY BANK WILL REJECT:
    - CIBIL score 548 — below minimum threshold for most business loans
    - Business revenue declining 3 years in a row (35% drop)
    - Business current account frequently overdrawn
    - GST filings late/missing for 4 months out of 12
    - Existing business loan already in restructuring (NPA risk)
    - Requesting Rs. 15,00,000 on a business with Rs. 8,000/month net profit
    - Personal guarantor (spouse) also has poor credit score 562
    - No audited financials — only self-declared income figures
    """
    base = OUTPUT_DIR / "06_struggling_business"
    print("Generating: BAD PROFILE — Meena Pillai, 41 (Struggling business, bank rejection expected)")

    _make_pdf(base / "business_income_statement.pdf", "Business Income Statement — FY 2025-26", [
        ("Business Details", [
            ["Proprietor", "Meena Pillai"], ["Business Name", "Pillai Textiles & Sarees"],
            ["Business Type", "Sole Proprietorship — Retail Garments"],
            ["GST Registration", "TSTGST27XYZAB9K1"], ["Years in Operation", "6 years"],
            ["Business Status", "DECLINING — third consecutive year of falling revenue"],
        ]),
        ("Revenue Trend (Declining)", [
            ["Annual Revenue FY 2022-23", "Rs. 42,00,000"],
            ["Annual Revenue FY 2023-24", "Rs. 31,00,000 (-26% YoY)"],
            ["Annual Revenue FY 2024-25", "Rs. 22,00,000 (-29% YoY)"],
            ["Annual Revenue FY 2025-26 (projected)", "Rs. 15,00,000 (-32% YoY)"],
        ]),
        ("Current Year P&L (FY 2025-26)", [
            ["Revenue", "Rs. 15,00,000"], ["Cost of Goods Sold", "Rs. 11,80,000"],
            ["Gross Profit", "Rs. 3,20,000"], ["Operating Expenses", "Rs. 2,24,000"],
            ["Net Profit", "Rs. 96,000 (Rs. 8,000/month)"],
            ["Net Profit Margin", "6.4% (down from 18.2% three years ago)"],
        ]),
        ("Notes", [
            ["Audit Status", "Accounts NOT audited — self-declared figures only"],
            ["Reason for Decline", "Competition from online retail; no digital presence"],
        ]),
    ])

    _make_pdf(base / "bank_statement.pdf", "Current Account Statement — Q1 2026", [
        ("Account Summary", [
            ["Account Holder", "Pillai Textiles & Sarees"], ["Account Type", "Current Account"],
            ["Average Monthly Balance", "Rs. 12,000 (frequently overdrawn)"],
            ["Opening Balance (Jan)", "Rs. 8,500"],
            ["Closing Balance (Mar)", "Rs. -3,200 (overdrawn)"],
        ]),
        ("Monthly Cash Flow", [
            ["Avg. Monthly Inflow (Sales)", "Rs. 1,25,000"],
            ["Avg. Monthly Outflow (Purchases + Expenses)", "Rs. 1,18,000"],
            ["Avg. Monthly Net Cash Flow", "Rs. 7,000 (barely positive)"],
            ["Overdraft Instances (Q1)", "4 instances, totalling Rs. 28,500"],
            ["Bank Charges (Q1)", "Rs. 2,200 (overdraft + penalty charges)"],
        ]),
        ("Risk Flags", [
            ["Outward cheque returns", "2 cheques bounced in Feb 2026"],
            ["Large unexplained cash withdrawals", "Rs. 85,000 in Jan 2026"],
            ["Irregular deposit pattern", "Deposits inconsistent — some months near zero"],
        ]),
    ])

    _make_pdf(base / "gst_summary.pdf", "GST Filing Summary — FY 2025-26", [
        ("GST Compliance", [
            ["GSTIN", "TSTGST27XYZAB9K1"],
            ["Total Outward Supply (Annual)", "Rs. 15,00,000"],
            ["Total Tax Paid", "Rs. 1,35,000"],
            ["Returns Filed on Time", "8 out of 12 months"],
            ["Late Filings", "April, August, November 2025 and January 2026"],
            ["Late Fee Paid", "Rs. 8,000 (accumulated penalties)"],
            ["GSTR-9 Annual Return", "NOT FILED for FY 2024-25 (overdue)"],
        ]),
        ("Compliance Risk", [
            ["Filing Consistency", "Poor — 33% of returns filed late"],
            ["Assessment", "High compliance risk; may attract GST audit"],
        ]),
    ])

    _make_pdf(base / "credit_score_report.pdf", "Credit Score Report", [
        ("Business Owner Credit Summary", [
            ["Credit Score (CIBIL) — Personal", "548"],
            ["Score Band", "Poor — High Risk"],
            ["Total Active Accounts", "4"],
            ["Credit Card Utilisation", "72%"],
            ["Payment History", "3 late payments; 1 restructured account"],
            ["Existing Business Loan", "Rs. 9,50,000 outstanding — RESTRUCTURED"],
            ["Personal Guarantor (Spouse)", "CIBIL 562 — also Poor"],
        ]),
        ("Risk Indicators", [
            ["Business Loan Status", "RESTRUCTURED under RBI guidelines — high NPA risk"],
            ["Debt-to-Income Ratio", "Approx. 118% of monthly business profit"],
            ["Number of Hard Enquiries (6 months)", "5 (multiple lender rejections)"],
            ["Previous Loan Applications", "Rejected by 3 banks in last 6 months"],
            ["Recommendation", "DECLINE — business viability in question"],
        ]),
    ])

    _make_pdf(base / "existing_loan_statement.pdf", "Existing Loan Statement — Business Loan (Restructured)", [
        ("Loan Details", [
            ["Lender", "Test Bank Ltd."], ["Loan Type", "Business Term Loan"],
            ["Original Amount", "Rs. 15,00,000"], ["Outstanding Balance", "Rs. 9,50,000"],
            ["Monthly EMI (Revised)", "Rs. 18,500 (down from Rs. 28,000 pre-restructure)"],
            ["Interest Rate", "14% p.a."],
            ["Restructuring Date", "September 2025"],
            ["Reason for Restructuring", "Business cash flow deterioration"],
            ["Repayment Status", "Current post-restructure but 90-day window only"],
            ["NPA Classification Risk", "HIGH — under watch list"],
        ]),
    ])
    print()


def main():
    print("=" * 70)
    print("Generating 6 Fictional Test Customer Profiles")
    print("4 Good Profiles + 2 Bad Profiles (bank rejection scenarios)")
    print("=" * 70)
    print()
    profile_young_salaried()
    profile_mid_career()
    profile_small_business()
    profile_high_income()
    profile_bad_credit_individual()
    profile_bad_credit_business()
    print("=" * 70)
    print(f"All PDFs saved under: {OUTPUT_DIR.resolve()}")
    print("=" * 70)
    print()
    print("GOOD PROFILES (loan approval expected):")
    print("  01_young_salaried_employee   — CIBIL 742, building credit")
    print("  02_mid_career_professional   — CIBIL 801, strong profile")
    print("  03_small_business_owner      — CIBIL 695, fair credit")
    print("  04_high_income_customer      — CIBIL 835, excellent credit")
    print()
    print("BAD PROFILES (bank rejection expected):")
    print("  05_bad_credit_individual     — CIBIL 511, 3 active EMIs, 2 defaults,")
    print("                                 78% DTI, negative monthly surplus")
    print("  06_struggling_business       — CIBIL 548, declining revenue 3 yrs,")
    print("                                 restructured loan, 4 late GST filings")


if __name__ == "__main__":
    main()
