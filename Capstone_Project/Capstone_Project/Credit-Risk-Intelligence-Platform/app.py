# app.py — Credit Risk Intelligence Platform v3.0
# ============================================================
# Streamlit entry point.
# Run: streamlit run app.py
#
# v3.0: Added authentication gate (login/register) before the
# main app loads. Dual workflow: Customer vs Financial Institution,
# each preserving all v2.0 functionality.
# ============================================================
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.services.langsmith_setup import initialise as _init_langsmith
_init_langsmith()

from src.orchestrator.orchestrator import AgentOrchestrator
from src.models.schemas import PlatformState
from src.auth.security import decode_session_token
from ui.sidebar import render as render_sidebar
from ui.theme import inject_global_css

st.set_page_config(
    page_title="Credit Risk Intelligence Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()


def _init_state() -> None:
    if "platform_state" not in st.session_state:
        st.session_state["platform_state"] = PlatformState()
    if "orchestrator" not in st.session_state:
        st.session_state["orchestrator"] = AgentOrchestrator()
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Dashboard"


_init_state()
state:        PlatformState    = st.session_state["platform_state"]
orchestrator: AgentOrchestrator = st.session_state["orchestrator"]
state.vector_store_ready = orchestrator.vector_store_ready


# ── Authentication gate ─────────────────────────────────────────────────────
def _current_user():
    """Validates the JWT in session_state on every rerun (handles expiry)."""
    token = st.session_state.get("auth_token")
    if not token:
        return None
    decoded = decode_session_token(token)
    if not decoded:
        # Expired or tampered token — force re-login
        st.session_state.pop("auth_token", None)
        st.session_state.pop("user_session", None)
        return None
    return st.session_state.get("user_session")


user_session = _current_user()

if not user_session:
    from ui.pages.auth import render as render_auth
    render_auth()
    st.stop()

# ── Logged in: show account badge + logout in sidebar footer ───────────────
with st.sidebar:
    st.markdown(
        f"<div style='padding:8px 16px;font-size:0.78rem;color:rgba(255,255,255,0.55)'>"
        f"Signed in as<br><strong style='color:#fff'>{user_session.full_name}</strong><br>"
        f"<span style='font-size:0.68rem;opacity:0.7'>"
        f"{'🏦 ' + (user_session.institution_name or 'Institution') if user_session.account_type.value == 'institution' else '👤 Customer'}"
        f"</span></div>",
        unsafe_allow_html=True,
    )
    if st.button("🚪 Logout", use_container_width=True):
        for key in ("auth_token", "user_session", "platform_state", "orchestrator", "current_page"):
            st.session_state.pop(key, None)
        st.rerun()

state.account_type = user_session.account_type.value

# ── Navigation ────────────────────────────────────────────────────────────────
page = render_sidebar(state, account_type=user_session.account_type.value)

# ── Page routing ──────────────────────────────────────────────────────────────
match page:
    case "Dashboard":
        from ui.pages.dashboard import render
        render(state)

    case "Upload Documents":
        from ui.pages.upload import render
        render(state, orchestrator, account_type=user_session.account_type.value)

    case "Document Summary":
        from ui.pages.summary import render
        render(state)

    case "Risk Analysis":
        from ui.pages.risk_analysis import render
        render(state, orchestrator)

    case "AI Recommendations":
        from ui.pages.recommendations import render
        render(state, orchestrator)

    case "Retirement Planner":
        from ui.pages.retirement_planner import render
        render(state, orchestrator)

    case "AI Chat":
        from ui.pages.chat import render
        render(state, orchestrator)

    case _:
        st.error(f"Unknown page: {page}. Navigating to Dashboard.")
        st.session_state["current_page"] = "Dashboard"
        st.rerun()
