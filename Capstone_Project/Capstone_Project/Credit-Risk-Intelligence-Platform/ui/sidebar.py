# ui/sidebar.py — Enterprise Redesign v2.1 (with Retirement Planner)
from __future__ import annotations
import streamlit as st
from config.settings import settings
from src.models.schemas import PlatformState, ProcessingStatus, EntityType
from ui.theme import C

_PAGES = [
    "📊  Dashboard",
    "📤  Upload Documents",
    "📋  Document Summary",
    "🔍  Risk Analysis",
    "💡  AI Recommendations",
    "🏖️  Retirement Planner",
    "💬  AI Chat",
]

# FIX: split on double-space instead of slicing by character count
# emoji characters are multi-byte so p[4:] was cutting into the page name
_LABEL_TO_NAME = {p: p.split("  ", 1)[1] for p in _PAGES}
_NAME_TO_LABEL  = {v: k for k, v in _LABEL_TO_NAME.items()}


def render(state: PlatformState, account_type: str = "customer") -> str:
    """Render sidebar. Returns selected clean page name.
    account_type ('customer'/'institution') currently reuses the same
    page set — pages internally branch their content by account_type
    and entity_type rather than duplicating entire page files, per the
    'reuse existing components' requirement."""
    current_name  = st.session_state.get("current_page", "Dashboard")
    current_label = _NAME_TO_LABEL.get(current_name, _PAGES[0])

    with st.sidebar:
        _logo()
        _divider()
        _group_label("Main")
        selected_label = _nav(current_label)
        _divider()
        _status(state)
        _divider()
        _provider()

    name = _LABEL_TO_NAME.get(selected_label, "Dashboard")
    st.session_state["current_page"] = name
    return name


def _logo() -> None:
    st.markdown(
        f"""
        <div style='padding:20px 16px 14px 16px'>
          <div style='display:flex;align-items:center;gap:10px'>
            <div style='width:38px;height:38px;border-radius:10px;
                        background:linear-gradient(135deg,{C["blue"]},{C["teal"]});
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.25rem;flex-shrink:0'>🏦</div>
            <div>
              <div style='font-size:0.88rem;font-weight:700;color:#fff;
                          letter-spacing:-0.01em;line-height:1.15'>Credit Risk</div>
              <div style='font-size:0.62rem;color:rgba(255,255,255,0.4);
                          letter-spacing:0.1em;text-transform:uppercase'>
                Intelligence Platform</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _divider() -> None:
    st.markdown(
        f"<hr style='border:none;border-top:1px solid {C['shell_border']};"
        f"margin:4px 16px'>",
        unsafe_allow_html=True,
    )


def _group_label(text: str) -> None:
    st.markdown(
        f"<div style='font-size:0.6rem;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:0.12em;color:rgba(255,255,255,0.28);"
        f"padding:12px 20px 2px 20px'>{text}</div>",
        unsafe_allow_html=True,
    )


def _nav(current_label: str) -> str:
    try:
        idx = _PAGES.index(current_label)
    except ValueError:
        idx = 0
    selected = st.radio(
        "navigation",
        options=_PAGES,
        index=idx,
        label_visibility="collapsed",
        key="sidebar_radio",
    )
    return selected


def _status(state: PlatformState) -> None:
    st.markdown(
        "<div style='font-size:0.6rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.12em;color:rgba(255,255,255,0.28);"
        "padding:10px 20px 4px 20px'>Session</div>",
        unsafe_allow_html=True,
    )

    failed = sum(
        1 for d in state.documents
        if d.processing_status == ProcessingStatus.FAILED
    )
    retirement_status = "Ready" if state.retirement_result else "Pending"
    rows = [
        ("📄", "Documents",  str(state.total_documents()), ""),
        ("✅", "Processed",  str(state.processed_count()), ""),
        (
            "🔍", "Risk Score",
            f"{state.risk_assessment.risk_score:.0f}"
            if state.risk_assessment else "—",
            "",
        ),
        (
            "🏖️", "Retirement",
            retirement_status,
            C["success"] if state.retirement_result else "",
        ),
        (
            "💬", "Chat",
            "Ready" if state.vector_store_ready else "No",
            "",
        ),
    ]
    if failed:
        rows.append(("❌", "Errors", str(failed), C["danger"]))

    rows_html = ""
    for icon, label, val, val_color in rows:
        vc = f"color:{val_color};" if val_color else "color:rgba(255,255,255,0.9);"
        rows_html += (
            f"<div style='display:flex;justify-content:space-between;"
            f"align-items:center;padding:4px 20px'>"
            f"<span style='font-size:0.73rem;color:rgba(255,255,255,0.45)'>"
            f"{icon} {label}</span>"
            f"<span style='font-size:0.73rem;font-weight:700;{vc}'>{val}</span>"
            f"</div>"
        )
    st.markdown(
        f"<div style='padding-bottom:6px'>{rows_html}</div>",
        unsafe_allow_html=True,
    )


def _provider() -> None:
    provider  = settings.LLM_PROVIDER.upper()
    model     = settings.active_llm_model
    vs        = settings.VECTOR_STORE_PROVIDER.upper()
    dot_color = "#00875A" if settings.LLM_PROVIDER == "openai" else "#4285F4"
    st.markdown(
        f"<div style='margin:6px 12px 16px 12px;"
        f"background:rgba(255,255,255,0.04);"
        f"border-radius:8px;padding:10px 12px;"
        f"border:1px solid {C['shell_border']}'>"
        f"<div style='font-size:0.6rem;color:rgba(255,255,255,0.3);"
        f"text-transform:uppercase;letter-spacing:0.1em;"
        f"margin-bottom:5px'>AI Engine</div>"
        f"<div style='display:flex;align-items:center;gap:6px'>"
        f"<div style='width:7px;height:7px;border-radius:50%;"
        f"background:{dot_color};flex-shrink:0'></div>"
        f"<span style='font-size:0.78rem;font-weight:700;color:#fff'>"
        f"{provider}</span>"
        f"<span style='font-size:0.65rem;color:rgba(255,255,255,0.3);margin-left:auto'>"
        f"{vs}</span>"
        f"</div>"
        f"<div style='font-size:0.65rem;color:rgba(255,255,255,0.3);"
        f"margin-top:3px;font-family:JetBrains Mono,monospace'>"
        f"{model}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
