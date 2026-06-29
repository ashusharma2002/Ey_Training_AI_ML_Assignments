# src/ui/pages/recommendations.py  — Enterprise Redesign v2.0
from __future__ import annotations
import streamlit as st
from src.agents.orchestrator import AgentOrchestrator
from src.models.schemas import PlatformState
from src.ui.theme import C, checklist_item, empty_state, info_box, kpi_card, page_header, section_header


def render(state: PlatformState, orchestrator: AgentOrchestrator) -> None:
    page_header("AI Recommendations",
                "Personalised credit improvement plan, safer loan options, and next best actions.")

    if not state.summaries:
        empty_state("💡", "No Documents Available",
                    "Upload and process financial documents to receive AI-powered recommendations.")
        return

    col_btn, _ = st.columns([2, 3])
    with col_btn:
        if st.button("🤖  Generate Recommendations",
                     type="primary", use_container_width=True):
            with st.spinner("Generating personalised recommendations…"):
                if not state.risk_assessment:
                    orchestrator.run_risk_analysis(state)
                orchestrator.run_recommendations(state)
            st.success("✅  Recommendations ready.")
            st.rerun()

    st.markdown("---")

    if not state.recommendations:
        info_box("Click <strong>Generate Recommendations</strong> to receive your "
                 "personalised credit improvement plan, loan alternatives, and action steps.",
                 "info")
        return

    rec  = state.recommendations
    tabs = st.tabs(["✅  Credit Checklist", "🏦  Loan Options",
                    "📋  Financial Advice", "⚡  Next Actions"])

    with tabs[0]: _checklist(rec)
    with tabs[1]: _loans(rec)
    with tabs[2]: _advice(rec)
    with tabs[3]: _actions(rec)


# ── Checklist ─────────────────────────────────────────────────────────────────
def _checklist(rec) -> None:
    section_header("✅", "Credit Improvement Checklist")
    if not rec.credit_improvement_checklist:
        info_box("No checklist items generated.", "info"); return

    st.markdown(
        f"<p style='font-size:0.82rem;color:{C['text2']};margin-bottom:12px'>"
        f"Complete these steps to strengthen your credit profile.</p>",
        unsafe_allow_html=True,
    )
    for item in rec.credit_improvement_checklist:
        checklist_item(item)


# ── Loan options ──────────────────────────────────────────────────────────────
def _loans(rec) -> None:
    section_header("🏦", "Safer Loan Options")

    if rec.safer_loan_amount:
        st.markdown(
            f"<div style='background:linear-gradient(135deg,{C['shell']},{C['shell_hover']});"
            f"color:white;padding:20px 24px;border-radius:12px;margin-bottom:18px'>"
            f"<div style='font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;"
            f"opacity:0.5;margin-bottom:5px'>AI Recommended Safer Amount</div>"
            f"<div style='font-size:1.5rem;font-weight:800;letter-spacing:-0.02em'>"
            f"{rec.safer_loan_amount}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if not rec.alternative_loan_suggestions:
        info_box("No alternative loan suggestions available.", "info"); return

    for loan in rec.alternative_loan_suggestions:
        st.markdown(
            f"<div class='loan-card'>"
            f"<div class='loan-card-header'>"
            f"<div style='width:32px;height:32px;border-radius:8px;"
            f"background:{C['blue_dim']};display:flex;align-items:center;"
            f"justify-content:center;font-size:1rem'>🏦</div>"
            f"<span style='font-size:0.9rem;font-weight:700;color:{C['text']}'>"
            f"{loan.loan_type}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(kpi_card("Loan Amount", loan.amount, "",
                                 accent=C["blue"], icon="💰",
                                 icon_bg=C["blue_dim"]),
                        unsafe_allow_html=True)
        with c2:
            st.markdown(kpi_card("Interest Rate", loan.interest_rate_range, "estimated range",
                                 accent=C["gold"], icon="📊",
                                 icon_bg=C["gold_dim"]),
                        unsafe_allow_html=True)
        st.markdown(
            f"<div style='margin-top:10px;font-size:0.82rem;color:{C['text2']}'>"
            f"<strong style='color:{C['text']}'>Rationale:</strong> "
            f"{loan.rationale}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


# ── Financial advice ──────────────────────────────────────────────────────────
def _advice(rec) -> None:
    section_header("📋", "Financial Recommendations")
    if not rec.financial_recommendations:
        info_box("No financial recommendations generated.", "info"); return

    for i, txt in enumerate(rec.financial_recommendations, 1):
        st.markdown(
            f"<div style='display:flex;align-items:flex-start;gap:14px;"
            f"padding:14px 16px;background:{C['surface']};"
            f"border-radius:10px;border:1px solid {C['border']};margin:6px 0'>"
            f"<div style='width:28px;height:28px;border-radius:6px;"
            f"background:{C['gold_dim']};color:{C['gold']};"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-size:0.75rem;font-weight:800;flex-shrink:0'>{i:02d}</div>"
            f"<div style='font-size:0.875rem;color:{C['text']};line-height:1.6'>"
            f"{txt}</div></div>",
            unsafe_allow_html=True,
        )


# ── Next actions ──────────────────────────────────────────────────────────────
def _actions(rec) -> None:
    section_header("⚡", "Immediate Next Actions")
    if not rec.next_best_actions:
        info_box("No immediate actions identified.", "info"); return

    st.markdown(
        f"<p style='font-size:0.82rem;color:{C['text2']};margin-bottom:12px'>"
        f"Prioritise these actions to improve your loan application outcome.</p>",
        unsafe_allow_html=True,
    )
    priority = [C["danger"], C["warning"], C["warning"]]
    for i, action in enumerate(rec.next_best_actions, 1):
        acol = priority[i - 1] if i <= 3 else C["teal"]
        abg  = f"rgba({','.join(str(int(acol.lstrip('#')[j:j+2], 16)) for j in (0,2,4))},0.08)"
        st.markdown(
            f"<div class='action-item' style='border-left:3px solid {acol}'>"
            f"<div class='action-num' style='background:{abg};color:{acol}'>"
            f"#{i}</div>"
            f"<span style='font-size:0.875rem;color:{C['text']};line-height:1.55'>"
            f"{action}</span></div>",
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
