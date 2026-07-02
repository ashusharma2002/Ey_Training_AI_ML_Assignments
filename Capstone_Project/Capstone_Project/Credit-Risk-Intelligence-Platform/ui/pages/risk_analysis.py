# ui/pages/risk_analysis.py
from __future__ import annotations
import plotly.graph_objects as go
import streamlit as st
from src.orchestrator.orchestrator import AgentOrchestrator
from src.models.schemas import PlatformState
from ui.theme import (
    C, RISK_BG, RISK_COLORS,
    badge, empty_state, info_box, kpi_card,
    page_header, section_header,
)


def _missing_document_popup(state: PlatformState) -> None:
    """Phase 15 — intelligent popup showing what's missing before analysis runs."""
    from src.orchestrator.document_validator import run_validation
    alerts = run_validation(state)

    if not alerts:
        return

    high = [a for a in alerts if a.severity == "High"]
    other = [a for a in alerts if a.severity != "High"]

    with st.expander(
        f"⚠️ {len(alerts)} item(s) appear to be missing from your documents — click to review",
        expanded=bool(high),
    ):
        st.markdown(
            f"<p style='font-size:0.82rem;color:{C['text2']};margin-bottom:8px'>"
            f"Analysis will still run, but results may be less accurate without these. "
            f"This is a quick keyword-based check, not a guarantee — review and upload "
            f"more documents if anything below is genuinely missing.</p>",
            unsafe_allow_html=True,
        )
        for a in high + other:
            color = C["danger"] if a.severity == "High" else C["warning"]
            st.markdown(
                f"<div style='padding:8px 12px;margin:4px 0;border-left:3px solid {color};"
                f"background:{color}10;border-radius:0 6px 6px 0;font-size:0.82rem'>"
                f"<strong style='color:{color}'>{a.item}</strong> "
                f"<span style='font-size:0.7rem;color:{C['text3']}'>({a.severity} priority)</span>"
                f"<br><span style='color:{C['text2']}'>{a.why_needed}</span>"
                f"</div>",
                unsafe_allow_html=True,
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

    _missing_document_popup(state)

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

    if state.loan_context.is_loan_application:
        st.markdown("---")
        if state.account_type == "institution":
            _institution_loan_section(ra, state)
        else:
            _customer_loan_section(ra, state)

    st.markdown("---")
    _detail_tabs(ra)


def _customer_loan_section(ra, state) -> None:
    """Phase 9 — Enhanced Customer Risk Analysis display."""
    section_header("🏦", "Loan Application Assessment")
    lc = state.loan_context
    st.markdown(
        f"<p style='font-size:0.82rem;color:{C['text3']};margin-bottom:10px'>"
        f"Requested: ₹{lc.loan_amount:,.0f} · {lc.loan_type.value if lc.loan_type else ''}</p>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(kpi_card("Approval Probability", ra.approval_probability or "—", "",
                              accent=C["success"], icon="✅", icon_bg=C["teal_dim"]), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Interest Rate Range", ra.interest_rate_range or "—", "",
                              accent=C["gold"], icon="📊", icon_bg="rgba(245,166,35,0.12)"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Safe Borrowing Amount", ra.safe_borrowing_amount or "—", "",
                              accent=C["blue"], icon="💰", icon_bg=C["blue_dim"]), unsafe_allow_html=True)

    if ra.best_loan_type or ra.affordable_emi:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        c4, c5 = st.columns(2)
        with c4:
            if ra.best_loan_type:
                info_box(f"<strong>Best-fit loan type:</strong> {ra.best_loan_type}", "info")
        with c5:
            if ra.affordable_emi:
                info_box(f"<strong>Affordable EMI:</strong> {ra.affordable_emi}", "info")

    if ra.recommended_banks:
        st.markdown(f"<p style='font-size:0.82rem;font-weight:600;margin-top:10px'>Recommended Lender Types</p>", unsafe_allow_html=True)
        for bank in ra.recommended_banks:
            st.markdown(f"<div style='padding:6px 12px;background:{C['surface2']};border-radius:6px;"
                        f"margin:3px 0;font-size:0.8rem'>🏦 {bank}</div>", unsafe_allow_html=True)

    if ra.avoid_lenders_warning:
        info_box(f"⚠️ {ra.avoid_lenders_warning}", "warning")

    if ra.alternative_suggestions:
        st.markdown(f"<p style='font-size:0.82rem;font-weight:600;margin-top:10px'>Alternatives to Consider</p>", unsafe_allow_html=True)
        for s in ra.alternative_suggestions:
            st.markdown(f"<div style='padding:6px 12px;background:{C['teal_dim']};border-radius:6px;"
                        f"margin:3px 0;font-size:0.8rem'>💡 {s}</div>", unsafe_allow_html=True)


def _institution_loan_section(ra, state) -> None:
    """Phase 13 — Institution Risk Analysis (lender-focused) display."""
    section_header("🏛️", "Lender Risk Assessment")
    lc = state.loan_context
    st.markdown(
        f"<p style='font-size:0.82rem;color:{C['text3']};margin-bottom:10px'>"
        f"Applicant type: {lc.applicant_type.value if lc.applicant_type else '—'} · "
        f"Requested: ₹{lc.loan_amount:,.0f} · {lc.loan_type.value if lc.loan_type else ''}</p>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        cat_color = C["success"] if ra.risk_category and "Low" in ra.risk_category else C["warning"]
        st.markdown(kpi_card("Risk Category", ra.risk_category or "—", "",
                              color=cat_color, accent=cat_color, icon="🎯", icon_bg=C["blue_dim"]), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Default Risk", ra.default_risk or "—", "",
                              accent=C["danger"], icon="⚠️", icon_bg="rgba(222,53,11,0.1)"), unsafe_allow_html=True)
    with c3:
        conf = ra.confidence_score
        st.markdown(kpi_card("Confidence Score", f"{conf:.0f}/100" if conf is not None else "—", "",
                              accent=C["teal"], icon="🔍", icon_bg=C["teal_dim"]), unsafe_allow_html=True)

    for label, value in [
        ("Repayment Capacity", ra.repayment_capacity),
        ("Income Stability", ra.income_stability),
        ("Credit History", ra.credit_history_summary),
    ]:
        if value:
            info_box(f"<strong>{label}:</strong> {value}", "info")

    if ra.fraud_indicators:
        st.markdown(f"<p style='font-size:0.82rem;font-weight:600;color:{C['danger']};margin-top:10px'>🚩 Fraud Indicators Detected</p>", unsafe_allow_html=True)
        for f in ra.fraud_indicators:
            st.markdown(f"<div class='danger-box' style='margin:4px 0;padding:8px 12px;font-size:0.8rem'>🚩 {f}</div>",
                        unsafe_allow_html=True)
    else:
        info_box("✅ No fraud indicators detected in available data.", "success")


def _kpis(ra) -> None:
    lvl = ra.risk_level.value
    col = RISK_COLORS.get(lvl, C["text"])
    dti = ra.debt_to_income_ratio

    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        st.markdown(
            kpi_card("Risk Score", f"{ra.risk_score:.0f}", f"/ 100  ·  {lvl}",
                     color=col, accent=col, icon="🎯",
                     icon_bg=RISK_BG.get(lvl, C["blue_dim"])),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            kpi_card("Credit Health", ra.credit_health, "overall rating",
                     accent=C["teal"], icon="💳", icon_bg=C["teal_dim"]),
            unsafe_allow_html=True,
        )
    with c3:
        # BUG FIX: was using substring match `"Eligible" in text`, which
        # incorrectly colored "Conditionally Eligible" the same bright
        # green as a clean "Eligible" — visually inconsistent with the
        # cautionary nature of "conditional" status. Now uses precise
        # matching: full success only for an exact/clean eligible status.
        elig_text = ra.loan_eligibility.strip()
        elig_lower = elig_text.lower()
        if elig_lower in ("eligible", "eligible for additional capital"):
            elig_col = C["success"]
        elif "not" in elig_lower or "not recommended" in elig_lower:
            elig_col = C["danger"]
        elif "condition" in elig_lower:
            elig_col = C["warning"]   # amber, not green — it's cautionary
        else:
            elig_col = C["text"]      # neutral navy, matches other cards

        st.markdown(
            kpi_card("Loan Eligibility", elig_text, "",
                     color=elig_col, accent=elig_col, icon="🏦",
                     icon_bg="rgba(0,135,90,0.1)"),
            unsafe_allow_html=True,
        )
    with c4:
        # BUG FIX: previously always showed "Debt-to-Income" — meaningless
        # for a bank/corporate (always rendered "N/A"). Now uses the
        # entity-appropriate key_metrics field if present (CRAR/NPA for
        # banks, D/E for corporates), falling back to DTI only when no
        # key_metrics were generated (e.g. individual borrower).
        if ra.key_metrics:
            metric = ra.key_metrics[0]
            m_color = (
                C["success"] if metric.is_good is True
                else C["danger"] if metric.is_good is False
                else C["gold"]
            )
            st.markdown(
                kpi_card(metric.label, metric.value, "from uploaded documents",
                         color=m_color, accent=m_color, icon="📊",
                         icon_bg="rgba(245,166,35,0.12)"),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                kpi_card("Debt-to-Income",
                         f"{dti:.1%}" if dti is not None else "N/A",
                         "lower is better",
                         accent=C["gold"], icon="📊",
                         icon_bg="rgba(245,166,35,0.12)"),
                unsafe_allow_html=True,
            )


def _gauge(ra) -> None:
    section_header("🎯", "Risk Score")
    lvl  = ra.risk_level.value
    gcol = RISK_COLORS.get(lvl, "#888")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=ra.risk_score,
        number={"suffix": " / 100", "font": {"size": 32, "family": "Inter", "color": gcol}},
        title={"text": f"<b>{lvl} Risk</b>", "font": {"size": 13, "color": gcol}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": C["border"],
                     "tickvals": [0, 30, 60, 80, 100],
                     "ticktext": ["0", "Low", "Moderate", "High", "100"]},
            "bar":       {"color": gcol, "thickness": 0.28},
            "bgcolor":   "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  30], "color": "rgba(0,135,90,0.10)"},
                {"range": [30, 60], "color": "rgba(255,139,0,0.10)"},
                {"range": [60, 80], "color": "rgba(224,123,0,0.10)"},
                {"range": [80,100], "color": "rgba(222,53,11,0.10)"},
            ],
            "threshold": {"line": {"color": gcol, "width": 3}, "thickness": 0.8, "value": ra.risk_score},
        },
    ))
    fig.update_layout(height=280, margin={"l": 20, "r": 20, "t": 60, "b": 10},
                      paper_bgcolor="rgba(0,0,0,0)", font={"family": "Inter, sans-serif"})
    st.plotly_chart(fig, use_container_width=True)

    interpretations = {
        "Low":      ("🟢", "Low Risk",      "Strong financial profile. Loan approval likely.",                 C["success"]),
        "Moderate": ("🟡", "Moderate Risk",  "Acceptable profile with some areas to improve.",                C["warning"]),
        "High":     ("🟠", "High Risk",      "Significant weaknesses. Conditional approval only.",            "#E07B00"),
        "Critical": ("🔴", "Critical Risk",  "Serious red flags. Loan not recommended currently.",            C["danger"]),
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


def _risk_breakdown_chart(ra) -> None:
    section_header("📊", "Risk Breakdown")
    n_s, n_w, n_r, n_m = len(ra.strengths), len(ra.weaknesses), len(ra.red_flags), len(ra.missing_information)
    categories = ["Missing Info", "Red Flags", "Weaknesses", "Strengths"]
    values     = [n_m, n_r, n_w, n_s]
    colors     = [C["text3"], C["danger"], C["warning"], C["success"]]
    text_labels = [
        f"{n_m} item{'s' if n_m != 1 else ''}",
        f"{n_r} flag{'s' if n_r != 1 else ''}",
        f"{n_w} item{'s' if n_w != 1 else ''}",
        f"{n_s} item{'s' if n_s != 1 else ''}",
    ]
    fig = go.Figure(go.Bar(
        x=values, y=categories, orientation="h",
        marker_color=colors, text=text_labels, textposition="outside",
        textfont={"size": 11, "family": "Inter"},
        hovertemplate="%{y}: %{x}<extra></extra>",
    ))
    fig.update_layout(
        xaxis={"title": "Count", "showgrid": True, "gridcolor": C["border"],
               "zeroline": False, "range": [0, max(max(values) + 2, 6)]},
        yaxis={"showgrid": False, "tickfont": {"size": 12, "family": "Inter"}},
        height=240, margin={"l": 10, "r": 60, "t": 10, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif", "color": C["text"]},
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    total_positive = n_s
    total_negative = n_w + n_r
    if total_positive > total_negative:
        msg   = f"✅ Positive signals outweigh concerns — **{n_s} strengths** vs **{total_negative} negatives**."
        style = C["success"]
    elif total_negative > total_positive:
        msg   = f"⚠️ More concerns than strengths — **{total_negative} negatives** vs **{n_s} strengths**."
        style = C["warning"]
    else:
        msg   = f"⚖️ Balanced profile — equal strengths and concerns (**{n_s} each**)."
        style = C["blue"]
    st.markdown(
        f"<div style='padding:10px 14px;background:{style}12;"
        f"border-left:3px solid {style};border-radius:0 8px 8px 0;"
        f"font-size:0.84rem;color:{C['text']};margin-top:4px'>"
        f"{msg}</div>",
        unsafe_allow_html=True,
    )


def _detail_tabs(ra) -> None:
    tabs = st.tabs(["✅  Strengths", "⚠️  Weaknesses", "🚩  Red Flags", "❓  Missing Info"])

    def _rows(items, variant):
        icons = {"success": "✅", "warning": "⚠️", "danger": "🚩", "info": "❓"}
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
