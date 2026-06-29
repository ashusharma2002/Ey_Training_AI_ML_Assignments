# src/ui/pages/risk_analysis.py
# ============================================================
# Risk Analysis page — replaced confusing radar chart with
# meaningful, readable charts that show real data.
# ============================================================
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.agents.orchestrator import AgentOrchestrator
from src.models.schemas import PlatformState
from src.ui.theme import (
    C, RISK_BG, RISK_COLORS,
    badge, empty_state, info_box, kpi_card,
    page_header, section_header,
)


def render(state: PlatformState, orchestrator: AgentOrchestrator) -> None:
    page_header(
        "Risk Analysis",
        "AI-powered credit risk scoring, financial health assessment, and red-flag detection.",
    )

    if not state.summaries:
        empty_state(
            "🔍", "No Documents to Analyse",
            "Upload and process financial documents first, then run Risk Analysis.",
        )
        return

    # ── Action bar ────────────────────────────────────────────
    col_btn, col_ts = st.columns([2, 3], gap="large")
    with col_btn:
        if st.button(
            "🔄  Run / Refresh Risk Analysis",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("AI is scoring your financial documents…"):
                orchestrator.run_risk_analysis(state)
            st.success("✅  Risk analysis complete.")
            st.rerun()
    with col_ts:
        if state.risk_assessment:
            ts = state.risk_assessment.assessed_at.strftime("%d %b %Y, %H:%M UTC")
            st.markdown(
                f"<div style='padding:10px 14px;background:{C['surface2']};"
                f"border-radius:8px;border:1px solid {C['border']};"
                f"font-size:0.8rem;color:{C['text2']}'>"
                f"🕐  Last assessed: <strong>{ts}</strong></div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    if not state.risk_assessment:
        info_box(
            "Click <strong>Run / Refresh Risk Analysis</strong> above to generate "
            "an AI-powered credit risk report.",
            "info",
        )
        return

    ra = state.risk_assessment

    _kpis(ra)
    st.markdown("---")

    col_g, col_b = st.columns([1, 1], gap="large")
    with col_g:
        _gauge(ra)
    with col_b:
        _risk_breakdown_chart(ra)

    st.markdown("---")
    _detail_tabs(ra)


# ── KPIs ──────────────────────────────────────────────────────────────────────

def _kpis(ra) -> None:
    lvl = ra.risk_level.value
    col = RISK_COLORS.get(lvl, C["text"])
    dti = ra.debt_to_income_ratio

    c1, c2, c3, c4 = st.columns(4, gap="small")

    with c1:
        st.markdown(
            kpi_card(
                "Risk Score", f"{ra.risk_score:.0f}",
                f"/ 100  ·  {lvl}",
                color=col, accent=col,
                icon="🎯", icon_bg=RISK_BG.get(lvl, C["blue_dim"]),
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            kpi_card(
                "Credit Health", ra.credit_health, "overall rating",
                accent=C["teal"], icon="💳", icon_bg=C["teal_dim"],
            ),
            unsafe_allow_html=True,
        )
    with c3:
        elig_col = C["success"] if "Eligible" in ra.loan_eligibility else C["warning"]
        st.markdown(
            kpi_card(
                "Loan Eligibility", ra.loan_eligibility, "",
                color=elig_col, accent=elig_col,
                icon="🏦", icon_bg="rgba(0,135,90,0.1)",
            ),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            kpi_card(
                "Debt-to-Income",
                f"{dti:.1%}" if dti is not None else "N/A",
                "lower is better",
                accent=C["gold"], icon="📊",
                icon_bg="rgba(245,166,35,0.12)",
            ),
            unsafe_allow_html=True,
        )


# ── Gauge ─────────────────────────────────────────────────────────────────────

def _gauge(ra) -> None:
    section_header("🎯", "Risk Score")
    lvl  = ra.risk_level.value
    gcol = RISK_COLORS.get(lvl, "#888")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=ra.risk_score,
        number={
            "suffix": " / 100",
            "font": {"size": 32, "family": "Inter", "color": gcol},
        },
        title={
            "text": f"<b>{lvl} Risk</b>",
            "font": {"size": 13, "color": gcol},
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": C["border"],
                "tickvals": [0, 30, 60, 80, 100],
                "ticktext": ["0", "Low", "Moderate", "High", "100"],
            },
            "bar":       {"color": gcol, "thickness": 0.28},
            "bgcolor":   "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  30], "color": "rgba(0,135,90,0.10)"},
                {"range": [30, 60], "color": "rgba(255,139,0,0.10)"},
                {"range": [60, 80], "color": "rgba(224,123,0,0.10)"},
                {"range": [80,100], "color": "rgba(222,53,11,0.10)"},
            ],
            "threshold": {
                "line": {"color": gcol, "width": 3},
                "thickness": 0.8,
                "value": ra.risk_score,
            },
        },
    ))
    fig.update_layout(
        height=280,
        margin={"l": 20, "r": 20, "t": 60, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    st.plotly_chart(fig, use_container_width=True)

    # Plain-language interpretation below gauge
    interpretations = {
        "Low":      ("🟢", "Low Risk", "Strong financial profile. Loan approval likely.", C["success"]),
        "Moderate": ("🟡", "Moderate Risk", "Acceptable profile with some areas to improve.", C["warning"]),
        "High":     ("🟠", "High Risk", "Significant weaknesses. Conditional approval only.", "#E07B00"),
        "Critical": ("🔴", "Critical Risk", "Serious red flags. Loan not recommended currently.", C["danger"]),
    }
    dot, label, note, color = interpretations.get(lvl, ("⚪", lvl, "", C["text3"]))
    st.markdown(
        f"<div style='text-align:center;padding:10px 16px;"
        f"background:{color}14;border:1px solid {color}30;"
        f"border-radius:8px;margin-top:-8px'>"
        f"<span style='font-size:1.1rem'>{dot}</span> "
        f"<strong style='color:{color}'>{label}</strong> — "
        f"<span style='font-size:0.83rem;color:{C['text2']}'>{note}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ── Risk Breakdown Bar Chart (replaces radar) ─────────────────────────────────

def _risk_breakdown_chart(ra) -> None:
    section_header("📊", "Risk Breakdown")

    n_strengths  = len(ra.strengths)
    n_weaknesses = len(ra.weaknesses)
    n_red_flags  = len(ra.red_flags)
    n_missing    = len(ra.missing_information)

    # Horizontal bar chart — each bar is a real count from the AI assessment
    categories = [
        "Missing Info",
        "Red Flags",
        "Weaknesses",
        "Strengths",
    ]
    values = [n_missing, n_red_flags, n_weaknesses, n_strengths]
    colors = [
        C["text3"],          # Missing — neutral grey
        C["danger"],         # Red flags — red
        C["warning"],        # Weaknesses — orange
        C["success"],        # Strengths — green
    ]
    text_labels = [
        f"{n_missing} item{'s' if n_missing != 1 else ''}",
        f"{n_red_flags} flag{'s' if n_red_flags != 1 else ''}",
        f"{n_weaknesses} item{'s' if n_weaknesses != 1 else ''}",
        f"{n_strengths} item{'s' if n_strengths != 1 else ''}",
    ]

    fig = go.Figure(go.Bar(
        x=values,
        y=categories,
        orientation="h",
        marker_color=colors,
        text=text_labels,
        textposition="outside",
        textfont={"size": 11, "family": "Inter"},
        hovertemplate="%{y}: %{x}<extra></extra>",
    ))

    fig.update_layout(
        xaxis={
            "title": "Count",
            "showgrid": True,
            "gridcolor": C["border"],
            "zeroline": False,
            "range": [0, max(max(values) + 2, 6)],
        },
        yaxis={
            "showgrid": False,
            "tickfont": {"size": 12, "family": "Inter"},
        },
        height=240,
        margin={"l": 10, "r": 60, "t": 10, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif", "color": C["text"]},
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Plain-language callout box below chart
    total_positive = n_strengths
    total_negative = n_weaknesses + n_red_flags
    if total_positive > total_negative:
        msg   = f"✅ Positive signals outweigh concerns — **{n_strengths} strengths** vs **{total_negative} negatives**."
        style = C["success"]
    elif total_negative > total_positive:
        msg   = f"⚠️ More concerns than strengths — **{total_negative} negatives** vs **{n_strengths} strengths**."
        style = C["warning"]
    else:
        msg   = f"⚖️ Balanced profile — equal strengths and concerns (**{n_strengths} each**)."
        style = C["blue"]

    st.markdown(
        f"<div style='padding:10px 14px;background:{style}12;"
        f"border-left:3px solid {style};border-radius:0 8px 8px 0;"
        f"font-size:0.84rem;color:{C['text']};margin-top:4px'>"
        f"{msg}</div>",
        unsafe_allow_html=True,
    )


# ── Detail Tabs ───────────────────────────────────────────────────────────────

def _detail_tabs(ra) -> None:
    tabs = st.tabs([
        "✅  Strengths",
        "⚠️  Weaknesses",
        "🚩  Red Flags",
        "❓  Missing Info",
    ])

    def _rows(items, variant):
        icons = {
            "success": "✅",
            "warning": "⚠️",
            "danger":  "🚩",
            "info":    "❓",
        }
        ic = icons.get(variant, "•")
        if not items:
            info_box("None identified.", "info")
            return
        for item in items:
            st.markdown(
                f"<div class='{variant}-box' style='margin:4px 0;padding:10px 14px;"
                f"font-size:0.875rem;line-height:1.55'>"
                f"{ic} &nbsp;{item}</div>",
                unsafe_allow_html=True,
            )

    with tabs[0]: _rows(ra.strengths,           "success")
    with tabs[1]: _rows(ra.weaknesses,          "warning")
    with tabs[2]: _rows(ra.red_flags,           "danger")
    with tabs[3]: _rows(ra.missing_information, "info")
