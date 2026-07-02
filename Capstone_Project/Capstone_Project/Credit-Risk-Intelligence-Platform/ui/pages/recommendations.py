# ui/pages/recommendations.py — v2.0 with 4 new modules
from __future__ import annotations
import plotly.graph_objects as go
import streamlit as st
from src.orchestrator.orchestrator import AgentOrchestrator
from src.models.schemas import EntityType, PlatformState, RiskLevel
from ui.theme import C, checklist_item, empty_state, info_box, kpi_card, page_header, section_header

# Priority colors as safe tuples (avoids hex-parse bug in old code)
_PRIORITY_COLORS = {
    "High":   (C["danger"],  "rgba(222,53,11,0.08)"),
    "Medium": (C["warning"], "rgba(255,139,0,0.08)"),
    "Low":    (C["teal"],    "rgba(0,180,166,0.08)"),
}
_DEFAULT_COLOR = (C["teal"], "rgba(0,180,166,0.08)")

_INSTITUTIONAL_TYPES = (
    EntityType.COMMERCIAL_BANK,
    EntityType.NBFC,
    EntityType.LARGE_CORPORATE,
    EntityType.SME,
)


def _is_institutional(state: PlatformState) -> bool:
    """True for banks/NBFCs/corporates — drives label switching so an
    HDFC-scale entity sees 'Capital Strategies' instead of 'Loan Options'
    with personal-loan-scale amounts."""
    if not state.combined_summary:
        return False
    return state.combined_summary.entity_type in _INSTITUTIONAL_TYPES


def _has_sufficient_data(state: PlatformState) -> bool:
    """
    Conditional display guard: return True only when documents have
    enough information to generate meaningful recommendations.
    Prevents empty or generic recommendations from confusing users.
    """
    if not state.risk_assessment:
        return False
    ra = state.risk_assessment
    # If risk score is exactly 50 (default fallback) or too many missing items → insufficient
    if ra.risk_score == 50.0 and ra.credit_health == "Assessment failed — re-run analysis.":
        return False
    if len(ra.missing_information) > 4:
        return False
    return True


def render(state: PlatformState, orchestrator: AgentOrchestrator) -> None:
    page_header(
        "AI Recommendations",
        "Personalised credit improvement plan, safer loan options, and action steps.",
    )

    if not state.summaries:
        empty_state(
            "💡", "No Documents Available",
            "Upload and process financial documents to receive AI-powered recommendations.",
        )
        return

    col_btn, _ = st.columns([2, 3])
    with col_btn:
        if st.button(
            "🤖  Generate Recommendations",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Generating personalised recommendations…"):
                if not state.risk_assessment:
                    orchestrator.run_risk_analysis(state)
                orchestrator.run_recommendations(state)
            st.success("✅  Recommendations ready.")
            st.rerun()

    st.markdown("---")

    if not state.recommendations:
        info_box(
            "Click <strong>Generate Recommendations</strong> to receive your "
            "personalised credit improvement plan.",
            "info",
        )
        return

    rec = state.recommendations
    institutional = _is_institutional(state)

    if rec.institution_decision:
        _institution_decision_banner(rec)

    # Main tabs — labels adapt for institutional entities (bank/corporate)
    tabs = st.tabs([
        "✅  " + ("Action Checklist" if institutional else "Credit Checklist"),
        "🏦  " + ("Capital Strategies" if institutional else "Loan Options"),
        "📋  Financial Advice",
        "⚡  Urgency Actions",
        "📈  Risk Simulator",
    ])

    with tabs[0]: _checklist(rec)
    with tabs[1]: _loans(rec, institutional)
    with tabs[2]: _advice(rec)
    with tabs[3]: _urgency(rec, state)
    with tabs[4]: _risk_simulator(rec, state)


def _institution_decision_banner(rec) -> None:
    """Phase 14 — prominent loan officer decision banner."""
    decision = rec.institution_decision
    decision_colors = {
        "Approve": (C["success"], "✅"),
        "Approve with conditions": (C["warning"], "⚠️"),
        "Request additional documents": (C["blue"], "📄"),
        "Reduce loan amount": (C["warning"], "📉"),
        "Require collateral": (C["warning"], "🔒"),
        "Recommend guarantor": (C["warning"], "👥"),
        "Reject with explanation": (C["danger"], "🔴"),
    }
    color, icon = decision_colors.get(decision, (C["text3"], "ℹ️"))

    st.markdown(
        f"<div style='padding:18px 22px;background:{color}12;"
        f"border:1px solid {color}30;border-radius:12px;border-left:5px solid {color};"
        f"margin-bottom:16px'>"
        f"<div style='font-size:0.68rem;letter-spacing:0.1em;text-transform:uppercase;"
        f"color:{color};font-weight:700;margin-bottom:4px'>Loan Officer Recommendation</div>"
        f"<div style='font-size:1.1rem;font-weight:800;color:{color};margin-bottom:6px'>"
        f"{icon} {decision}</div>"
        f"<div style='font-size:0.85rem;color:{C['text']}'>{rec.institution_decision_reasoning or ''}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if rec.institution_conditions:
        st.markdown(f"<p style='font-size:0.82rem;font-weight:600;margin-bottom:6px'>Conditions to Satisfy</p>",
                    unsafe_allow_html=True)
        for c in rec.institution_conditions:
            st.markdown(f"<div style='padding:6px 12px;background:{C['surface2']};border-radius:6px;"
                        f"margin:3px 0;font-size:0.82rem'>☑️ {c}</div>", unsafe_allow_html=True)

    if rec.applicant_improvement_tips:
        st.markdown(f"<p style='font-size:0.82rem;font-weight:600;margin:10px 0 6px 0'>Tips for the Applicant</p>",
                    unsafe_allow_html=True)
        for tip in rec.applicant_improvement_tips:
            st.markdown(f"<div style='padding:6px 12px;background:{C['teal_dim']};border-radius:6px;"
                        f"margin:3px 0;font-size:0.82rem'>💡 {tip}</div>", unsafe_allow_html=True)
    st.markdown("---")


def _checklist(rec) -> None:
    section_header("✅", "Credit Improvement Checklist")
    if not rec.credit_improvement_checklist:
        info_box("No checklist items generated.", "info")
        return
    st.markdown(
        f"<p style='font-size:0.82rem;color:{C['text2']};margin-bottom:12px'>"
        f"Complete these steps in order to strengthen your credit profile.</p>",
        unsafe_allow_html=True,
    )
    for item in rec.credit_improvement_checklist:
        checklist_item(item)


def _loans(rec, institutional: bool = False) -> None:
    section_title  = "Capital & Funding Strategies" if institutional else "Safer Loan Options"
    banner_label   = "AI Recommended Capital Buffer" if institutional else "AI Recommended Safer Amount"
    card_icon      = "🏛️" if institutional else "🏦"
    type_label     = "Strategy / Instrument" if institutional else "Loan Type"
    amount_label   = "Scale" if institutional else "Loan Amount"
    rate_label     = "Target Rate / Coupon" if institutional else "Interest Rate"
    empty_msg      = "No capital strategy suggestions available." if institutional else "No alternative loan suggestions available."

    section_header("🏦", section_title)

    if rec.safer_loan_amount:
        st.markdown(
            f"<div style='background:linear-gradient(135deg,{C['shell']},{C['shell_hover']});"
            f"color:white;padding:20px 24px;border-radius:12px;margin-bottom:18px'>"
            f"<div style='font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;"
            f"opacity:0.5;margin-bottom:5px'>{banner_label}</div>"
            f"<div style='font-size:1.4rem;font-weight:800;letter-spacing:-0.02em'>"
            f"{rec.safer_loan_amount}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if not rec.alternative_loan_suggestions:
        info_box(empty_msg, "info")
        return

    for loan in rec.alternative_loan_suggestions:
        urgency    = getattr(loan, "urgency", "Medium")
        color, bg  = _PRIORITY_COLORS.get(urgency, _DEFAULT_COLOR)  # FIXED: no hex parsing
        st.markdown(
            f"<div class='loan-card'><div class='loan-card-header'>"
            f"<div style='width:32px;height:32px;border-radius:8px;"
            f"background:{C['blue_dim']};display:flex;align-items:center;"
            f"justify-content:center;font-size:1rem'>{card_icon}</div>"
            f"<span style='font-size:0.9rem;font-weight:700;color:{C['text']}'>"
            f"{loan.loan_type}</span>"
            f"<span style='margin-left:auto;font-size:0.72rem;padding:2px 8px;"
            f"border-radius:12px;background:{bg};color:{color};font-weight:700'>"
            f"{urgency} Priority</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                kpi_card(amount_label, loan.amount, "", accent=C["blue"], icon="💰", icon_bg=C["blue_dim"]),
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                kpi_card(rate_label, loan.interest_rate_range, "estimated range",
                         accent=C["gold"], icon="📊", icon_bg="rgba(245,166,35,0.12)"),
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div style='margin-top:10px;font-size:0.82rem;color:{C['text2']}'>"
            f"<strong style='color:{C['text']}'>Why this works:</strong> "
            f"{loan.rationale}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


def _advice(rec) -> None:
    section_header("📋", "Financial Recommendations")
    if not rec.financial_recommendations:
        info_box("No financial recommendations generated.", "info")
        return
    for i, txt in enumerate(rec.financial_recommendations, 1):
        st.markdown(
            f"<div style='display:flex;align-items:flex-start;gap:14px;"
            f"padding:14px 16px;background:{C['surface']};"
            f"border-radius:10px;border:1px solid {C['border']};margin:6px 0'>"
            f"<div style='width:28px;height:28px;border-radius:6px;"
            f"background:rgba(245,166,35,0.12);color:{C['gold']};"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-size:0.75rem;font-weight:800;flex-shrink:0'>{i:02d}</div>"
            f"<div style='font-size:0.875rem;color:{C['text']};line-height:1.6'>"
            f"{txt}</div></div>",
            unsafe_allow_html=True,
        )


def _urgency(rec, state: PlatformState) -> None:
    """Urgency Pipeline Sorting — only shown when risk_score > 40."""
    section_header("⚡", "Urgency Pipeline")

    if not state.risk_assessment or state.risk_assessment.risk_score <= 40:
        info_box(
            "Urgency sorting is shown when risk score is above 40. "
            "Your current profile looks manageable — focus on the checklist above.",
            "info",
        )
        return

    if not _has_sufficient_data(state):
        info_box(
            "Upload more complete financial documents to unlock urgency-sorted action items.",
            "info",
        )
        return

    actions = rec.urgency_sorted_actions or []
    if not actions:
        # Fall back to next_best_actions with default urgency levels
        actions = [
            {"action": a, "urgency": ["High", "Medium", "Low"][min(i, 2)],
             "timeline": ["This week", "This month", "3-6 months"][min(i, 2)], "impact": ""}
            for i, a in enumerate(rec.next_best_actions)
        ]

    if not actions:
        info_box("No urgency actions generated.", "info")
        return

    for item in actions:
        urgency   = item.get("urgency", "Medium")
        timeline  = item.get("timeline", "")
        action    = item.get("action", "")
        impact    = item.get("impact", "")
        color, bg = _PRIORITY_COLORS.get(urgency, _DEFAULT_COLOR)

        impact_html = (
            f"<div style='font-size:0.78rem;color:var(--text3);margin-top:4px'>Impact: {impact}</div>"
            if impact else ""
        )
        html = (
            f"<div style='display:flex;align-items:flex-start;gap:14px;"
            f"padding:14px 16px;background:{C['surface']};"
            f"border-radius:10px;border:1px solid {C['border']};margin:6px 0;"
            f"border-left:3px solid {color}'>"
            f"<div>"
            f"<div style='display:flex;gap:8px;margin-bottom:4px'>"
            f"<span style='font-size:0.72rem;padding:2px 8px;border-radius:12px;"
            f"background:{bg};color:{color};font-weight:700'>{urgency}</span>"
            f"<span style='font-size:0.72rem;color:{C['text3']}'>{timeline}</span>"
            f"</div>"
            f"<div style='font-size:0.875rem;color:{C['text']};line-height:1.6'>{action}</div>"
            + impact_html
            + "</div></div>"
        )
        st.markdown(html, unsafe_allow_html=True)


def _risk_simulator(rec, state: PlatformState) -> None:
    """Long-Term Risk Simulator — shows projected risk improvement over time."""
    section_header("📈", "Long-Term Risk Simulator")

    if not state.risk_assessment:
        info_box("Run Risk Analysis first to see the risk simulator.", "info")
        return

    if not _has_sufficient_data(state):
        info_box(
            "Upload more complete financial documents to unlock the Risk Simulator.",
            "info",
        )
        return

    current_score = state.risk_assessment.risk_score
    sim_data      = rec.risk_simulator_data

    # Build default projection if AI didn't generate one
    if not sim_data:
        sim_data = [
            {"year": 0, "risk_score": current_score, "action": "Current"},
            {"year": 1, "risk_score": max(current_score - 12, 15), "action": "After 1 year of improvement"},
            {"year": 2, "risk_score": max(current_score - 22, 15), "action": "After 2 years"},
            {"year": 3, "risk_score": max(current_score - 30, 15), "action": "After 3 years"},
        ]

    years   = [d.get("year", i) for i, d in enumerate(sim_data)]
    scores  = [d.get("risk_score", current_score) for d in sim_data]
    actions = [d.get("action", "") for d in sim_data]

    # Color gradient based on final score
    final_score = scores[-1] if scores else current_score
    if final_score < 30:
        line_color = C["success"]
    elif final_score < 60:
        line_color = C["warning"]
    else:
        line_color = C["danger"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=scores,
        mode="lines+markers+text",
        line={"color": line_color, "width": 3, "shape": "spline"},
        marker={"size": 10, "color": line_color, "line": {"width": 2, "color": "white"}},
        text=[f"{s:.0f}" for s in scores],
        textposition="top center",
        hovertemplate="Year %{x}: Risk Score %{y:.0f}<br>%{customdata}<extra></extra>",
        customdata=actions,
    ))

    # Add risk zone backgrounds
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,135,90,0.05)",  line_width=0)
    fig.add_hrect(y0=30, y1=60,  fillcolor="rgba(255,139,0,0.05)", line_width=0)
    fig.add_hrect(y0=60, y1=80,  fillcolor="rgba(224,123,0,0.05)", line_width=0)
    fig.add_hrect(y0=80, y1=100, fillcolor="rgba(222,53,11,0.05)", line_width=0)

    fig.update_layout(
        xaxis={"title": "Year", "tickmode": "array", "tickvals": years,
               "gridcolor": C["border"], "showgrid": True},
        yaxis={"title": "Risk Score (lower is better)", "range": [0, 105],
               "gridcolor": C["border"], "showgrid": True},
        height=320,
        margin={"l": 40, "r": 30, "t": 20, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif", "color": C["text"]},
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    improvement = current_score - final_score
    if improvement > 0:
        st.markdown(
            f"<div style='padding:10px 14px;background:{C['success']}12;"
            f"border-left:3px solid {C['success']};border-radius:0 8px 8px 0;"
            f"font-size:0.84rem;color:{C['text']}'>"
            f"📉 Following the recommendations above could reduce your risk score by "
            f"<strong>{improvement:.0f} points</strong> over {years[-1]} year(s)."
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        f"<div style='background:{C['surface2']};padding:12px 16px;"
        f"border-radius:8px;border:1px solid {C['border']};"
        f"font-size:0.78rem;color:{C['text3']};text-align:center'>"
        f"⚠️ These AI-generated recommendations are advisory only. "
        f"Always consult a qualified financial advisor before making lending decisions."
        f"</div>",
        unsafe_allow_html=True,
    )
