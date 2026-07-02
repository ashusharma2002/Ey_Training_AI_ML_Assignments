# src/prompts/question_prompts.py
# ============================================================
# v3.2 — tighter prompt to reduce unanswerable suggestions.
#
# ROOT CAUSE of "some questions have no answer":
#   The original prompt asked the AI to generate questions based
#   on a summary of the document, not the actual raw text. So the
#   AI would write questions using terms it invented in the summary
#   (e.g. "SIP contributions", "Capital Adequacy Ratio") even when
#   those exact words never appeared in the uploaded PDFs. The
#   question would then fail retrieval silently.
#
# FIX 1 (this file): the prompt now explicitly includes a sample of
#   the actual extracted text and requires questions to only use
#   terms/phrases provably present in that sample — making it far
#   less likely the AI asks about concepts not in the documents.
#
# FIX 2 (chat_agent.py): fallback questions are also validated;
#   the validation threshold is stricter (financial keywords required,
#   not just content length > 50 chars); and unvalidated questions
#   are NEVER shown even when is_validated=False.
# ============================================================
from __future__ import annotations

QUESTION_GENERATION_SYSTEM = (
    "You design financial analysis questions for a RAG chatbot. "
    "The chatbot searches uploaded PDF documents for exact answers. "
    "CRITICAL: every question you write MUST be answerable by finding "
    "specific text in the document sample provided — never ask about "
    "concepts or figures not visible in that sample."
)


def build_question_generation_prompt(
    combined_summary: dict,
    document_names:   list[str],
    risk_score:       float | None = None,
    raw_text_sample:  str = "",   # NEW: actual extracted text for grounding
) -> str:
    entity_type   = combined_summary.get("entity_type", "Unknown")
    exec_overview = combined_summary.get("executive_overview", "")
    fin_position  = combined_summary.get("financial_position", "")
    docs_list     = "\n".join(f"- {d}" for d in document_names)
    risk_context  = f"\nRisk Score: {risk_score:.0f}/100" if risk_score is not None else ""

    # Include actual text so the AI is grounded in real document content
    text_section = ""
    if raw_text_sample.strip():
        text_section = f"""
ACTUAL DOCUMENT TEXT SAMPLE (questions MUST use terms from this):
---
{raw_text_sample[:2500]}
---
"""

    return f"""Generate 10 questions for a RAG chatbot that searches financial PDFs.

ENTITY TYPE: {entity_type}
DOCUMENTS UPLOADED:
{docs_list}{risk_context}

FINANCIAL OVERVIEW:
{exec_overview[:800]}
{fin_position[:800]}
{text_section}
STRICT RULES — read these carefully before generating questions:

1. GROUNDED IN ACTUAL TEXT: every question must use words and figures that
   appear in the document text sample above. Do NOT invent topics that are
   not visible there. If the sample shows "net profit" and "credit score",
   ask about those — NOT about SIP, CRAR, or balance sheets unless those
   exact words appear.

2. FACTUAL AND SPECIFIC: the chatbot searches for text, not reasons.
   GOOD: "What is the credit score reported in the document?"
   GOOD: "What is the net salary shown on the salary slip?"
   BAD:  "Should I increase my SIP?" (chatbot cannot answer — needs reasoning)
   BAD:  "What caused the profit to decline?" (requires analysis, not retrieval)
   BAD:  "How can I reduce my EMI?" (advice question — no specific text to find)

3. SHORT AND DIRECT: a good question is 8-15 words, asks for one specific fact.

4. DO NOT ask about information that is clearly absent from the text sample.
   If there is no bank statement data in the sample, do not ask about cash flow.
   If there is no ITR data, do not ask about tax returns.

5. 5 questions from a LENDER / analyst perspective (risk, income, liabilities)
   5 questions from the ENTITY's perspective (what does this mean for me?)

Respond ONLY in valid JSON (no markdown fences, no extra text):
{{
  "analyst_questions": ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"],
  "entity_questions":  ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"],
  "document_types":    ["type 1", "type 2"],
  "entity_type":       "{entity_type}"
}}"""
