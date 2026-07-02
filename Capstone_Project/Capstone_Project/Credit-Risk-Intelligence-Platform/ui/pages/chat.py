# ui/pages/chat.py — with validated suggested questions
from __future__ import annotations
import streamlit as st
from src.orchestrator.orchestrator import AgentOrchestrator
from src.models.schemas import EntityType, PlatformState
from ui.theme import C, empty_state, page_header, section_header


def render(state: PlatformState, orchestrator: AgentOrchestrator) -> None:
    page_header(
        "AI Chat Assistant",
        "Ask questions about your documents. Every answer is grounded exclusively in your uploaded data.",
    )

    if not state.vector_store_ready:
        if state.documents and orchestrator.vector_store_error:
            empty_state(
                "🔴", "Chat Index Failed to Build",
                f"{orchestrator.vector_store_error} "
                f"Go to Upload Documents to see details, fix the issue, then click "
                f"'Process Documents' again.",
            )
        else:
            empty_state(
                "💬", "Chat Not Ready Yet",
                "Upload and process at least one financial document to enable the AI assistant.",
            )
        return

    _smart_prompts(state, orchestrator)
    st.markdown("---")
    _history(state)
    st.markdown("---")
    _input(state, orchestrator)


def _smart_prompts(state: PlatformState, orchestrator: AgentOrchestrator) -> None:
    qs = state.suggested_questions
    section_header("💡", "Suggested Questions")

    # Show entity type badge if questions are dynamically generated
    if qs.entity_type != EntityType.UNKNOWN and qs.is_generated:
        et       = qs.entity_type.value
        et_color = {
            "Commercial Bank":              C["blue"],
            "NBFC / Financial Institution": C["teal"],
            "Large Corporate":              "#6366f1",
            "SME / Small Business":         C["warning"],
            "Individual / Borrower":        C["success"],
        }.get(et, C["text3"])
        validated_badge = ""
        if qs.is_validated:
            validated_badge = (
                f"<span style='background:{C['success']}18;color:{C['success']};"
                f"font-size:0.65rem;padding:2px 8px;border-radius:10px;"
                f"border:1px solid {C['success']}30;margin-left:8px'>"
                f"✓ Pre-validated</span>"
            )
        st.markdown(
            f"<div style='display:inline-flex;align-items:center;gap:8px;"
            f"background:{et_color}18;border:1px solid {et_color}33;"
            f"border-radius:20px;padding:3px 12px;margin-bottom:12px'>"
            f"<div style='width:7px;height:7px;border-radius:50%;"
            f"background:{et_color}'></div>"
            f"<span style='font-size:0.73rem;font-weight:700;color:{et_color}'>"
            f"Tailored for: {et}</span>"
            f"{validated_badge}"
            f"</div>",
            unsafe_allow_html=True,
        )

    col_a, col_e = st.columns(2, gap="large")
    # HARD RULE: never show a question that wasn't proven answerable.
    # The previous code fell back to a hardcoded generic question list
    # here whenever qs.analyst_questions was empty — but that list was
    # NEVER validated against the actual uploaded documents, silently
    # reintroducing the exact bug fixed in chat_agent.py's validation
    # logic. Now an empty validated list means: show nothing, not a guess.
    questions_a = qs.analyst_questions
    questions_e = qs.entity_questions

    # HARD RULE: never show questions that were not validated against the
    # actual uploaded documents. If is_validated is False it means the
    # vector store was not ready when questions were generated — showing
    # those questions would violate the guarantee that every suggestion
    # has a proven answer.
    if qs.is_generated and not qs.is_validated:
        st.markdown(
            f"<div style='padding:12px 16px;background:{C['surface2']};"
            f"border-radius:8px;border:1px dashed {C['border']};"
            f"font-size:0.82rem;color:{C['text3']};text-align:center'>"
            f"⏳ Suggested questions are being validated against your documents. "
            f"Run <strong>Risk Analysis</strong> first to generate verified questions, "
            f"or type your own question below."
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    if not questions_a and not questions_e and qs.is_generated:
        st.markdown(
            f"<div style='padding:12px 16px;background:{C['surface2']};"
            f"border-radius:8px;border:1px dashed {C['border']};"
            f"font-size:0.82rem;color:{C['text3']};text-align:center'>"
            f"No suggested questions could be confidently answered from your "
            f"uploaded documents yet. Try asking your own question below — "
            f"every answer is still grounded strictly in your documents."
            f"</div>",
            unsafe_allow_html=True,
        )

    with col_a:
        st.markdown(
            f"<div style='font-size:0.65rem;font-weight:700;color:{C['text3']};"
            f"text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px'>"
            f"🏦  Analyst / Lender</div>",
            unsafe_allow_html=True,
        )
        for i, q in enumerate(questions_a):
            if st.button(f"↗  {q}", key=f"aq_{i}", use_container_width=True):
                _send(q, state, orchestrator)
                st.rerun()

    with col_e:
        st.markdown(
            f"<div style='font-size:0.65rem;font-weight:700;color:{C['text3']};"
            f"text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px'>"
            f"👤  Entity / Borrower</div>",
            unsafe_allow_html=True,
        )
        for i, q in enumerate(questions_e):
            if st.button(f"↗  {q}", key=f"eq_{i}", use_container_width=True):
                _send(q, state, orchestrator)
                st.rerun()

    if qs.is_generated:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("🔄  Regenerate Questions", key="regen_q"):
            with st.spinner("Generating new questions based on your documents…"):
                try:
                    orchestrator.refresh_intelligence(state)
                except Exception as exc:
                    st.warning(f"Could not regenerate: {exc}")
            st.rerun()


def _history(state: PlatformState) -> None:
    section_header("📝", "Conversation")

    if not state.chat_history:
        st.markdown(
            f"<div style='text-align:center;padding:40px 24px;"
            f"background:{C['surface2']};border-radius:12px;"
            f"border:1px dashed {C['border']}'>"
            f"<div style='font-size:2rem;opacity:0.35;margin-bottom:8px'>🤖</div>"
            f"<div style='font-size:0.875rem;color:{C['text3']}'>"
            f"Select a question above or type your own below.<br>"
            f"<span style='font-size:0.78rem'>All answers are based exclusively on "
            f"your uploaded documents.</span></div></div>",
            unsafe_allow_html=True,
        )
        return

    for msg in state.chat_history:
        if msg.role == "user":
            st.markdown(
                f"<div class='chat-bubble-user'>"
                f"<div class='chat-meta' style='color:rgba(255,255,255,0.6)'>You</div>"
                f"{msg.content}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='chat-bubble-assistant'>"
                f"<div class='chat-meta' style='color:{C['blue']}'>"
                f"🤖  AI Assistant</div>",
                unsafe_allow_html=True,
            )
            # Render markdown so the 4-section format renders properly
            st.markdown(msg.content)

            if msg.sources:
                clean = [
                    s for s in msg.sources
                    if s and not s.startswith("tmp") and len(s) > 4
                ] or msg.sources[:3]
                srcs = "  ·  ".join(f"📄 {s}" for s in clean[:4])
                st.markdown(
                    f"<div class='chat-source'>Sources: {srcs}</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    col_clr, _ = st.columns([1, 4])
    with col_clr:
        if st.button("🗑️  Clear Chat", use_container_width=True):
            state.chat_history.clear()
            st.rerun()


def _input(state: PlatformState, orchestrator: AgentOrchestrator) -> None:
    section_header("✏️", "Ask a Question")

    with st.form("chat_form", clear_on_submit=True):
        question = st.text_area(
            "Question",
            placeholder=(
                "Ask anything about the uploaded financial documents…\n"
                "e.g. 'What was the net profit?' or 'Are there any red flags in the documents?'"
            ),
            height=90,
            label_visibility="collapsed",
        )
        c_send, c_note = st.columns([1, 4])
        with c_send:
            submitted = st.form_submit_button("Send  ↗", type="primary", use_container_width=True)
        with c_note:
            st.markdown(
                f"<div style='padding:8px 0;font-size:0.75rem;color:{C['text3']}'>"
                f"🔒  Grounded in your documents only.</div>",
                unsafe_allow_html=True,
            )

    if submitted and question.strip():
        with st.spinner("Searching your documents…"):
            _send(question.strip(), state, orchestrator)
        st.rerun()


def _send(question: str, state: PlatformState, orchestrator: AgentOrchestrator) -> None:
    orchestrator.chat(question, state)


def _default_analyst_questions() -> list[str]:
    return [
        "What is the total revenue or interest income reported?",
        "What are the total assets and liabilities?",
        "Is there evidence of consistent positive cash flow?",
        "What is the debt position of this entity?",
        "Are there any financial red flags in the documents?",
    ]


def _default_entity_questions() -> list[str]:
    return [
        "What is my overall financial health based on these documents?",
        "What are my biggest financial strengths?",
        "How much loan am I eligible for based on this data?",
        "What should I improve to get better credit terms?",
        "What does the balance sheet or financial summary show?",
    ]
