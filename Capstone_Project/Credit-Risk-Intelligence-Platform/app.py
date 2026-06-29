# app.py
# ============================================================
# Credit Risk Intelligence Platform — Main Application Entry
#
# Launch with:
#   streamlit run app.py
#
# IMPORTANT: Configure .env before running.
# See .env.example for all available options.
# ============================================================

from __future__ import annotations

import sys
from pathlib import Path

# ── Path setup — must come before any src imports ──────────────────────────
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

# ── Streamlit page config — must be first Streamlit call ───────────────────
st.set_page_config(
    page_title="Credit Risk Intelligence Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help":    "https://github.com/Chaurasiyakash0136/EY-Training-2026",
        "Report a bug":"https://github.com/Chaurasiyakash0136/EY-Training-2026/issues",
        "About":       "**Credit Risk Intelligence Platform** — Enterprise MVP\nPowered by AI agents and RAG.",
    },
)

# ── LangSmith observability — must be initialised before LangChain imports ──
# This writes LANGCHAIN_* env vars so LangChain auto-traces all LLM calls.
# If LANGCHAIN_API_KEY is not set in .env, this is a silent no-op.
from src.services.langsmith_setup import initialise as _init_langsmith
_init_langsmith()

# ── Application imports ────────────────────────────────────────────────────
from src.agents.orchestrator import AgentOrchestrator
from src.models.schemas import PlatformState
from src.ui import sidebar
from src.ui.theme import inject_global_css
from src.ui.pages import (
    chat,
    dashboard,
    recommendations,
    risk_analysis,
    summary,
    upload,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ── Session state ──────────────────────────────────────────────────────────

def _init_session() -> tuple[PlatformState, AgentOrchestrator]:
    """Initialise persistent session objects (once per browser session)."""
    if "platform_state" not in st.session_state:
        st.session_state["platform_state"] = PlatformState()
        logger.info("New PlatformState created.")

    if "orchestrator" not in st.session_state:
        st.session_state["orchestrator"] = AgentOrchestrator()
        logger.info("AgentOrchestrator created.")

    return (
        st.session_state["platform_state"],
        st.session_state["orchestrator"],
    )


# ── Router ─────────────────────────────────────────────────────────────────

_PAGE_MAP = {
    "Dashboard":          dashboard.render,
    "Upload Documents":   upload.render,
    "Document Summary":   summary.render,
    "Risk Analysis":      risk_analysis.render,
    "AI Recommendations": recommendations.render,
    "AI Chat":            chat.render,
}

# Pages whose render() accepts (state, orchestrator)
_ORCHESTRATOR_PAGES = {
    "Upload Documents",
    "Risk Analysis",
    "AI Recommendations",
    "AI Chat",
}


def _render_page(
    page_name: str,
    state: PlatformState,
    orchestrator: AgentOrchestrator,
) -> None:
    render_fn = _PAGE_MAP.get(page_name, dashboard.render)
    if page_name in _ORCHESTRATOR_PAGES:
        render_fn(state, orchestrator)
    else:
        render_fn(state)


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    inject_global_css()
    state, orchestrator = _init_session()
    current_page = sidebar.render(state)

    try:
        _render_page(current_page, state, orchestrator)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Page render error on '%s': %s", current_page, exc)
        st.error(
            f"⚠️ An error occurred: `{exc}`\n\n"
            "Check your API keys in `.env` and ensure documents are valid PDFs."
        )
        if st.button("🔄 Reload page"):
            st.rerun()


if __name__ == "__main__":
    main()
