# src/ui/pages/summary.py
# ============================================================
# Document Summary — Combined view + individual tabs.
# Updated: proper markdown rendering, readable typography,
# financial figures highlighted, better visual hierarchy.
# ============================================================
from __future__ import annotations

import streamlit as st

from src.models.schemas import EntityType, PlatformState
from src.ui.theme import C, empty_state, info_box, page_header, section_header


def render(state: PlatformState) -> None:
    page_header(
        "Document Summary",
        "AI-generated combined financial analysis across all uploaded documents.",
    )

    if not state.summaries:
        empty_state(
            "📋", "No Summaries Available",
            "Upload and process your financial documents to see "
            "AI-generated executive summaries, financial analysis, "
            "and key insights here.",
        )
        return

    # ── Tabs: Combined first, then individual documents ───────
    tab_labels = ["📊 Combined Analysis"] + [
        f"📄 {n[:20]}" for n in state.summaries.keys()
    ]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        _combined(state)

    for i, (name, summary) in enumerate(state.summaries.items(), start=1):
        with tabs[i]:
            _individual(name, summary)


# ── Combined Summary ──────────────────────────────────────────────────────────

def _combined(state: PlatformState) -> None:
    cs = state.combined_summary

    if cs is None:
        info_box(
            "Combined analysis is being generated. "
            "If this persists after processing, re-upload your documents.",
            "warning",
        )
        return

    # Entity type badge + document list
    et = cs.entity_type.value
    et_color = {
        "Commercial Bank":              C["blue"],
        "NBFC / Financial Institution": C["teal"],
        "Large Corporate":              "#6366f1",
        "SME / Small Business":         C["warning"],
        "Individual / Borrower":        C["success"],
    }.get(et, C["text3"])

    # Header row — entity badge + docs covered
    col_badge, col_docs = st.columns([1, 3], gap="small")
    with col_badge:
        st.markdown(
            f"<div style='background:{et_color}18;color:{et_color};"
            f"padding:6px 16px;border-radius:20px;font-size:0.8rem;"
            f"font-weight:700;border:1px solid {et_color}35;"
            f"display:inline-block;margin-top:4px'>"
            f"🏢 {et}</div>",
            unsafe_allow_html=True,
        )
    with col_docs:
        if cs.documents_covered:
            docs_html = " &nbsp;·&nbsp; ".join(
                f"<span style='color:{C['text2']}'>📄 {d}</span>"
                for d in cs.documents_covered
            )
            st.markdown(
                f"<div style='padding:8px 0;font-size:0.78rem'>{docs_html}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Executive Overview ────────────────────────────────────
    _section_card(
        icon="📑",
        title="Executive Overview",
        content=cs.executive_overview,
        accent=C["blue"],
    )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Financial Position + Income (2 columns) ───────────────
    col1, col2 = st.columns(2, gap="large")
    with col1:
        _section_card(
            icon="🏛️",
            title="Financial Position",
            content=cs.financial_position,
            accent=C["teal"],
        )
    with col2:
        _section_card(
            icon="📈",
            title="Income & Profitability",
            content=cs.income_profitability,
            accent="#6366f1",
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Strengths + Concerns (2 columns) ─────────────────────
    col3, col4 = st.columns(2, gap="large")
    with col3:
        _list_card(
            icon="✅",
            title="Key Strengths",
            items=cs.key_strengths,
            item_style="success",
            accent=C["success"],
        )
    with col4:
        _list_card(
            icon="⚠️",
            title="Areas of Concern",
            items=cs.areas_of_concern,
            item_style="warning",
            accent=C["warning"],
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Overall Assessment ────────────────────────────────────
    if cs.overall_assessment:
        section_header("🎯", "Overall Assessment")
        st.markdown(
            f"<div style='background:{C['blue_dim']};border-left:4px solid {C['blue']};"
            f"border-radius:0 10px 10px 0;padding:18px 22px;"
            f"font-size:0.92rem;line-height:1.75;color:{C['text']}'>"
            f"{cs.overall_assessment}</div>",
            unsafe_allow_html=True,
        )


# ── Card Helpers ──────────────────────────────────────────────────────────────

def _section_card(icon: str, title: str, content: str, accent: str) -> None:
    """
    Renders a titled card with markdown content.
    Uses st.markdown() for the body so **bold** and other formatting renders.
    """
    if not content:
        return

    section_header(icon, title)

    # Outer card container
    st.markdown(
        f"<div style='background:{C['surface']};border:1px solid {C['border']};"
        f"border-top:3px solid {accent};border-radius:0 0 10px 10px;"
        f"padding:16px 20px 4px 20px'>",
        unsafe_allow_html=True,
    )
    # Render content as markdown so **figures** are bold
    st.markdown(
        f"<div style='font-size:0.875rem;line-height:1.8;color:{C['text']}'>{content}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def _list_card(
    icon: str,
    title: str,
    items: list[str],
    item_style: str,
    accent: str,
) -> None:
    """Renders a titled card with a list of bullet items."""
    section_header(icon, title)

    if not items:
        info_box("None identified.", "info")
        return

    st.markdown(
        f"<div style='background:{C['surface']};border:1px solid {C['border']};"
        f"border-top:3px solid {accent};border-radius:0 0 10px 10px;"
        f"padding:12px 16px'>",
        unsafe_allow_html=True,
    )
    for item in items:
        bullet_icon = "✓" if item_style == "success" else "⚠"
        bullet_color = C["success"] if item_style == "success" else C["warning"]
        st.markdown(
            f"<div style='display:flex;gap:10px;align-items:flex-start;"
            f"padding:8px 0;border-bottom:1px solid {C['border']}'>"
            f"<span style='color:{bullet_color};font-weight:700;"
            f"flex-shrink:0;margin-top:1px'>{bullet_icon}</span>"
            f"<span style='font-size:0.855rem;line-height:1.6;color:{C['text']}'>"
            f"{item}</span></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


# ── Individual Document Summary ───────────────────────────────────────────────

def _individual(name: str, summary) -> None:
    sub_tabs = st.tabs([
        "🔍 Overview",
        "💰 Income & Expenses",
        "🏛️ Assets & Liabilities",
        "💧 Cash Flow",
        "📌 Key Insights",
    ])
    with sub_tabs[0]: _overview(summary)
    with sub_tabs[1]: _income_expenses(summary)
    with sub_tabs[2]: _assets_liabilities(summary)
    with sub_tabs[3]: _cash_flow(summary)
    with sub_tabs[4]: _insights(summary)


def _readable_card(content: str, border_color: str = "") -> None:
    """
    Renders a plain content card using st.markdown for proper formatting.
    Wraps in a styled container.
    """
    border = f"border-left:3px solid {border_color};" if border_color else ""
    st.markdown(
        f"<div style='background:{C['surface']};{border}"
        f"padding:16px 20px;border-radius:8px;"
        f"border:1px solid {C['border']};'>"
        f"<div style='font-size:0.875rem;line-height:1.8;color:{C['text']}'>"
        f"{content}</div></div>",
        unsafe_allow_html=True,
    )


def _overview(summary) -> None:
    section_header("📑", "Executive Summary")
    if summary.executive_summary:
        _readable_card(summary.executive_summary, C["blue"])
    else:
        info_box("Executive summary not available for this document.", "warning")

    if summary.financial_overview:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        section_header("📊", "Financial Overview")
        _readable_card(summary.financial_overview, C["teal"])


def _income_expenses(summary) -> None:
    c1, c2 = st.columns(2, gap="large")
    with c1:
        section_header("📈", "Income")
        if summary.income_summary:
            _readable_card(summary.income_summary, C["success"])
        else:
            info_box("Income data not available.", "info")
    with c2:
        section_header("📉", "Expenses")
        if summary.expense_summary:
            _readable_card(summary.expense_summary, C["warning"])
        else:
            info_box("Expense data not available.", "info")


def _assets_liabilities(summary) -> None:
    c1, c2 = st.columns(2, gap="large")
    with c1:
        section_header("🏦", "Assets")
        if summary.assets_summary:
            _readable_card(summary.assets_summary, C["success"])
        else:
            info_box("Assets data not available.", "info")
    with c2:
        section_header("⚖️", "Liabilities")
        if summary.liabilities_summary:
            _readable_card(summary.liabilities_summary, C["danger"])
        else:
            info_box("Liabilities data not available.", "info")


def _cash_flow(summary) -> None:
    section_header("💧", "Cash Flow Analysis")
    if summary.cash_flow_summary:
        _readable_card(summary.cash_flow_summary, C["blue"])
    else:
        info_box("Cash flow data not available for this document.", "info")


def _insights(summary) -> None:
    section_header("💡", "Key Financial Insights")
    if not summary.key_insights:
        info_box("No specific insights extracted from this document.", "info")
        return

    for i, insight in enumerate(summary.key_insights, 1):
        st.markdown(
            f"<div style='display:flex;align-items:flex-start;gap:14px;"
            f"padding:12px 16px;background:{C['surface']};"
            f"border-radius:10px;border:1px solid {C['border']};margin:6px 0'>"
            f"<div style='min-width:28px;height:28px;border-radius:50%;"
            f"background:{C['blue']};color:white;"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-size:0.72rem;font-weight:800;flex-shrink:0'>{i}</div>"
            f"<div style='font-size:0.875rem;color:{C['text']};line-height:1.65;"
            f"padding-top:3px'>{insight}</div></div>",
            unsafe_allow_html=True,
        )

    if summary.raw_extracted_text:
        with st.expander("🔍  View Raw Extracted Text", expanded=False):
            st.text_area(
                "",
                value=summary.raw_extracted_text[:5000],
                height=280,
                disabled=True,
                label_visibility="collapsed",
            )
