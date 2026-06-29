# src/ui/pages/dashboard.py  — Enterprise Redesign v2.0
from __future__ import annotations
import plotly.graph_objects as go
import streamlit as st
from src.models.schemas import PlatformState, ProcessingStatus
from src.ui.theme import C, COLORS, RISK_COLORS, RISK_BG, badge, empty_state, kpi_card, page_header, section_header


def render(state: PlatformState) -> None:
    page_header("Credit Risk Dashboard",
                "Real-time financial intelligence across all uploaded documents.")
    _kpi_row(state)
    st.markdown("---")
    col_left, col_right = st.columns([3, 2], gap="large")
    with col_left:
        _gauge(state)
    with col_right:
        _activity(state)
    st.markdown("---")
    _insights(state)


# ── KPI row ───────────────────────────────────────────────────────────────────
def _kpi_row(state: PlatformState) -> None:
    total     = state.total_documents()
    processed = state.processed_count()
    ra        = state.risk_assessment

    c1, c2, c3, c4, c5 = st.columns(5, gap="small")

    with c1:
        st.markdown(kpi_card("Total Documents", str(total), "uploaded",
                             accent=C["blue"], icon="📄", icon_bg=C["blue_dim"]),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Processed", str(processed), f"of {total} files",
                             accent=C["teal"], icon="✅", icon_bg=C["teal_dim"]),
                    unsafe_allow_html=True)
    with c3:
        if ra:
            score = ra.risk_score
            lvl   = ra.risk_level.value
            col   = RISK_COLORS.get(lvl, C["text"])
            st.markdown(kpi_card("Risk Score", f"{score:.0f}", lvl,
                                 color=col, accent=col,
                                 icon="🎯", icon_bg=RISK_BG.get(lvl, C["blue_dim"])),
                        unsafe_allow_html=True)
        else:
            st.markdown(kpi_card("Risk Score", "—", "Run analysis first",
                                 accent=C["border"], icon="🎯"),
                        unsafe_allow_html=True)
    with c4:
        if ra:
            st.markdown(kpi_card("Credit Health", ra.credit_health, "overall rating",
                                 accent=C["teal"], icon="💳", icon_bg=C["teal_dim"]),
                        unsafe_allow_html=True)
        else:
            st.markdown(kpi_card("Credit Health", "—", "Upload docs first",
                                 accent=C["border"], icon="💳"),
                        unsafe_allow_html=True)
    with c5:
        if ra:
            col5 = C["success"] if "Eligible" in ra.loan_eligibility else C["warning"]
            st.markdown(kpi_card("Loan Eligibility", ra.loan_eligibility, "",
                                 color=col5, accent=col5,
                                 icon="🏦", icon_bg=f"rgba(0,135,90,0.1)"),
                        unsafe_allow_html=True)
        else:
            st.markdown(kpi_card("Loan Eligibility", "—", "Pending",
                                 accent=C["border"], icon="🏦"),
                        unsafe_allow_html=True)


# ── Risk Gauge ────────────────────────────────────────────────────────────────
def _gauge(state: PlatformState) -> None:
    section_header("🎯", "Risk Overview")
    ra = state.risk_assessment

    if not ra:
        empty_state("📊", "No Risk Data Yet",
                    "Run Risk Analysis after uploading your financial documents.")
        return

    score = ra.risk_score
    lvl   = ra.risk_level.value
    gcol  = RISK_COLORS.get(lvl, "#888")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 48, "family": "Inter", "color": gcol},
                "suffix": ""},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis":  {"range": [0, 100], "tickwidth": 1,
                      "tickcolor": C["border"], "tickfont": {"size": 10}},
            "bar":   {"color": gcol, "thickness": 0.25},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  30], "color": "rgba(0,135,90,0.08)"},
                {"range": [30, 60], "color": "rgba(255,139,0,0.08)"},
                {"range": [60, 80], "color": "rgba(224,123,0,0.08)"},
                {"range": [80,100], "color": "rgba(222,53,11,0.08)"},
            ],
        },
    ))
    fig.update_layout(height=240, margin={"l": 16, "r": 16, "t": 16, "b": 0},
                      paper_bgcolor="rgba(0,0,0,0)",
                      font={"family": "Inter, sans-serif"})
    st.plotly_chart(fig, use_container_width=True)

    # Risk level pill
    pill_bg  = RISK_BG.get(lvl, "#eee")
    pill_col = RISK_COLORS.get(lvl, "#333")
    st.markdown(
        f"<div style='text-align:center;margin:-8px 0 16px 0'>"
        f"<span style='background:{pill_bg};color:{pill_col};padding:4px 18px;"
        f"border-radius:20px;font-size:0.78rem;font-weight:700;"
        f"text-transform:uppercase;letter-spacing:0.08em'>"
        f"{lvl} Risk</span></div>",
        unsafe_allow_html=True,
    )

    # Strengths / Red flags in two columns
    col_s, col_f = st.columns(2, gap="small")
    with col_s:
        st.markdown(f"<div style='font-size:0.72rem;font-weight:700;color:{C['teal']};"
                    f"text-transform:uppercase;letter-spacing:0.08em;"
                    f"margin-bottom:6px'>✅ Strengths</div>",
                    unsafe_allow_html=True)
        for s in (ra.strengths or ["None identified"])[:3]:
            st.markdown(f"<div class='success-box' style='margin:3px 0;padding:8px 12px;"
                        f"font-size:0.8rem'>• {s}</div>", unsafe_allow_html=True)
    with col_f:
        st.markdown(f"<div style='font-size:0.72rem;font-weight:700;color:{C['danger']};"
                    f"text-transform:uppercase;letter-spacing:0.08em;"
                    f"margin-bottom:6px'>🚩 Red Flags</div>",
                    unsafe_allow_html=True)
        for f in (ra.red_flags or ["None identified"])[:3]:
            st.markdown(f"<div class='danger-box' style='margin:3px 0;padding:8px 12px;"
                        f"font-size:0.8rem'>• {f}</div>", unsafe_allow_html=True)


# ── Activity ──────────────────────────────────────────────────────────────────
def _activity(state: PlatformState) -> None:
    section_header("📁", "Recent Activity")

    if not state.documents:
        empty_state("📂", "No Documents Yet",
                    "Upload financial PDFs to begin your analysis.")
        return

    for doc in reversed(state.documents[-8:]):
        s = doc.processing_status
        if s == ProcessingStatus.COMPLETE:
            b = badge("✓ Ready", "success")
        elif s == ProcessingStatus.PROCESSING:
            b = badge("⟳ Processing", "warning")
        elif s == ProcessingStatus.FAILED:
            b = badge("✗ Error", "danger")
        else:
            b = badge("○ Pending", "neutral")

        name = doc.file_name
        short = (name[:26] + "…") if len(name) > 28 else name
        st.markdown(
            f"<div class='activity-item'>"
            f"<span class='activity-name'>📄 {short}</span>"
            f"{b}</div>",
            unsafe_allow_html=True,
        )


# ── AI Insights ───────────────────────────────────────────────────────────────
def _insights(state: PlatformState) -> None:
    section_header("🤖", "AI Insights")

    if not state.summaries:
        empty_state("🧠", "AI Insights Pending",
                    "Process financial documents to unlock AI-generated insights, "
                    "trend analysis, and key financial observations.")
        return

    items = list(state.summaries.items())[:3]
    cols  = st.columns(len(items), gap="medium")

    for col, (name, summary) in zip(cols, items):
        with col:
            short_name = (name[:28] + "…") if len(name) > 30 else name
            st.markdown(
                f"<div class='insight-card'>"
                f"<div style='font-size:0.7rem;font-weight:700;color:{C['text3']};"
                f"text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px'>"
                f"📄 {short_name}</div>"
                f"<div style='font-size:0.82rem;color:{C['text']};line-height:1.55;"
                f"margin-bottom:10px'>"
                f"{summary.executive_summary or 'Summary pending...'}</div>",
                unsafe_allow_html=True,
            )
            if summary.key_insights:
                for ins in summary.key_insights[:3]:
                    st.markdown(
                        f"<div style='display:flex;gap:8px;margin:4px 0;"
                        f"font-size:0.78rem;color:{C['text2']}'>"
                        f"<span style='color:{C['teal']};flex-shrink:0'>›</span>"
                        f"<span>{ins}</span></div>",
                        unsafe_allow_html=True,
                    )
            st.markdown("</div>", unsafe_allow_html=True)
