# src/rag/prompt_builder.py
# ============================================================
# All LLM prompt templates in one place.
# ============================================================
from __future__ import annotations
from langchain_core.documents import Document
from src.utils.logger import get_logger

logger = get_logger(__name__)
_MAX_CHUNK_CHARS = 1200


def build_rag_prompt(
    question:       str,
    retrieved_docs: list[Document],
    system_context: str = "",
) -> str:
    if not retrieved_docs:
        context_block = "No relevant document context was found."
    else:
        chunks = []
        for i, doc in enumerate(retrieved_docs, start=1):
            source   = doc.metadata.get("source", "unknown")
            year     = doc.metadata.get("year", "")
            doc_type = doc.metadata.get("doc_type", "")
            label    = source
            if year:     label += f" ({year})"
            if doc_type: label += f" — {doc_type}"
            chunks.append(f"[Context {i} — {label}]\n{doc.page_content[:_MAX_CHUNK_CHARS]}")
        context_block = "\n\n".join(chunks)

    extra = f"\n\nAdditional context:\n{system_context}" if system_context else ""

    return f"""You are a Credit Risk Intelligence assistant for a commercial bank.

RULES:
- Answer using ONLY the document context below — never use general knowledge.
- If the answer is not in the context, say: "This information is not available in the uploaded documents."
- Format: use **bold** for all financial figures, bullet points for lists, tables for year comparisons.
- Always cite which document the data came from.{extra}

---DOCUMENT CONTEXT---
{context_block}
---END CONTEXT---

Question: {question}

Answer:"""


def build_summary_prompt(document_text: str, doc_type: str = "") -> str:
    type_hint = f"Document type: {doc_type}\n" if doc_type else ""
    return f"""You are a senior financial analyst. Analyse these financial document excerpts.

{type_hint}The text below contains excerpts sampled from different sections of the document.
Focus on actual financial figures, ratios, and data — ignore administrative/legal boilerplate.

---DOCUMENT EXCERPTS---
{document_text}
---END---

Respond in valid JSON (no markdown fences):
{{
  "executive_summary": "2-3 sentences: entity name, document period, headline financial result with specific figures",
  "financial_overview": "Overall financial position with actual numbers (assets, liabilities, equity)",
  "key_insights": ["Insight with specific figure 1", "Insight 2", "Insight 3", "Insight 4", "Insight 5"],
  "income_summary": "Revenue/income description with actual figures and year-on-year change",
  "expense_summary": "Expense description with actual figures",
  "assets_summary": "Assets description with actual figures",
  "liabilities_summary": "Liabilities description with actual figures",
  "cash_flow_summary": "Cash flow description with actual figures"
}}"""


def build_combined_summary_prompt(all_summaries: dict[str, str], all_text: str) -> str:
    summaries_block = "\n\n".join(
        f"=== {name} ===\n{text[:3000]}" for name, text in all_summaries.items()
    )
    n = len(all_summaries)
    return f"""You are a senior credit analyst writing a financial briefing for bank executives.

You have summaries and financial data from {n} document(s).
Write ONE combined analysis — not document by document.

FORMATTING RULES (critical):
- Wrap every financial figure, number, percentage in **bold**
- Example: Net profit was **₹44,108 crore**, up **19.8%** year-on-year
- Write 3-5 sentences per section
- Professional CFO-briefing tone

---DOCUMENT DATA---
{summaries_block}
---END---

Detect the entity type and respond in valid JSON (no markdown fences):
{{
  "executive_overview": "3-4 sentences covering entity name, reporting period, headline results with **bold figures**",
  "financial_position": "4-5 sentences on balance sheet: total assets, loans, deposits, capital. **Bold** all figures.",
  "income_profitability": "4-5 sentences on income, net profit, margins, YoY growth. **Bold** all figures.",
  "key_strengths": ["Strength with **specific figure**", "Strength 2", "Strength 3", "Strength 4"],
  "areas_of_concern": ["Concern with **specific figure** if available", "Concern 2", "Concern 3"],
  "overall_assessment": "2-3 sentences on overall financial health and outlook",
  "entity_type": "Commercial Bank | NBFC / Financial Institution | Large Corporate | SME / Small Business | Individual / Borrower | Unknown",
  "documents_covered": ["doc name 1", "doc name 2"]
}}"""


def build_question_generation_prompt(
    combined_summary: dict,
    document_names:   list[str],
    risk_score:       float | None = None,
) -> str:
    entity_type   = combined_summary.get("entity_type", "Unknown")
    exec_overview = combined_summary.get("executive_overview", "")
    fin_position  = combined_summary.get("financial_position", "")
    docs_list     = "\n".join(f"- {d}" for d in document_names)
    risk_context  = f"\nRisk Score: {risk_score:.0f}/100" if risk_score is not None else ""

    return f"""You are a financial analyst generating questions for a RAG-based credit risk chatbot.

The chatbot answers by searching document chunks for matching text — it CANNOT reason, calculate,
or infer. A question only gets an answer if the exact financial term appears in the document.

ENTITY: {entity_type}
DOCUMENTS:
{docs_list}{risk_context}

FINANCIAL CONTEXT:
{exec_overview}
{fin_position}

CRITICAL RULES — follow exactly:

1. QUESTION TYPE — every question must be FACTUAL and DIRECT, not analytical.
   ALLOWED starters: "What was", "What is", "What were", "How much", "What are", "What does"
   BANNED starters: "Why", "How did", "What caused", "What impact", "How will", "What effect"

   GOOD: "What was the net profit reported for FY2023?"
   BAD:  "What caused the net profit to increase in FY2023?"
   
   GOOD: "What are the total deposits as of March 31, 2023?"
   BAD:  "How did the deposit growth affect liquidity?"

2. USE ONLY CRORE VALUES — never use raw numbers in thousands or millions.
   If you see "1,461,285,166" in the data, that is in thousands = ₹1,461,285 crore.
   Always convert and write as "₹1,461,285 crore", never the raw number.

3. FINANCIAL TERMS — use the exact term that appears in the document:
   Bank terms: net profit, interest income, gross NPA, Capital Adequacy Ratio, net interest margin,
               total advances, total deposits, tier 1 capital, return on assets, earnings per share
   Corporate:  revenue, EBITDA, net profit, total assets, debt-to-equity, working capital
   Personal:   monthly income, total expenses, outstanding loans, savings balance

4. GROUP SPLIT:
   - Analyst/Lender: 5 questions a credit officer asks to evaluate lending risk
   - Entity/Borrower: 5 questions the entity asks about its own financial position
   Both groups must follow rules 1-3.

5. VARIETY — cover different financial topics across the 10 questions.
   Do not ask about the same metric twice.

Respond in valid JSON (no markdown fences):
{{
  "analyst_questions": ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"],
  "entity_questions":  ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"],
  "document_types":    ["type 1", "type 2"],
  "entity_type":       "{entity_type}"
}}"""


def build_risk_prompt(combined_text: str) -> str:
    return f"""You are a credit risk officer at a commercial bank.
Analyse the financial data and produce a risk assessment using ONLY data provided.
Do NOT estimate or fabricate figures not present in the text.

---FINANCIAL DATA---
{combined_text}
---END---

Respond in valid JSON (no markdown fences):
{{
  "risk_score": <0-100, higher = more risk>,
  "risk_level": "<Low|Moderate|High|Critical>",
  "credit_health": "<Excellent|Good|Fair|Poor|Critical>",
  "loan_eligibility": "<Eligible|Conditionally Eligible|Not Eligible>",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
  "red_flags": ["flag 1", "flag 2"],
  "missing_information": ["item 1", "item 2"],
  "debt_to_income_ratio": <number or null>,
  "monthly_income_estimate": <number or null>,
  "monthly_expense_estimate": <number or null>
}}"""


def build_recommendation_prompt(risk_assessment: dict, summary_texts: str) -> str:
    return f"""You are a credit counsellor. Generate personalised financial recommendations.

RISK ASSESSMENT:
{risk_assessment}

FINANCIAL SUMMARY:
{summary_texts[:4000]}

Respond in valid JSON (no markdown fences):
{{
  "credit_improvement_checklist": ["action 1", "action 2", "action 3", "action 4", "action 5"],
  "alternative_loan_suggestions": [
    {{"loan_type": "...", "amount": "...", "interest_rate_range": "...", "rationale": "..."}}
  ],
  "financial_recommendations": ["rec 1", "rec 2", "rec 3"],
  "safer_loan_amount": "₹X with reasoning",
  "next_best_actions": ["action 1", "action 2", "action 3"]
}}"""
