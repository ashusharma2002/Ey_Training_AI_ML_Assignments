# ui/pages/auth.py
# ============================================================
# Login / Create Account / Forgot Password screens.
# Shown BEFORE the main app when no user is logged in.
#
# v3.1 change: added account type badge to Login and Forgot
# Password tabs so the user always knows which portal they are
# on, not just on the Create Account tab.
# ============================================================
from __future__ import annotations
import streamlit as st
from src.auth import service
from src.auth.models import AccountType, UserSession
from ui.theme import C

try:
    from langsmith import trace as _ls_trace
    _TRACING = True
except ImportError:
    _TRACING = False


def _account_type_badge(tab_key: str) -> None:
    """
    Read-only account type selector shown on Login and Forgot Password
    tabs. tab_key must be unique per call site because Streamlit renders
    all tabs simultaneously and requires every widget key to be unique
    across the entire page, not just within the active tab.
    """
    selected = st.radio(
        "I am logging in as",
        options=[AccountType.CUSTOMER.value, AccountType.INSTITUTION.value],
        format_func=lambda x: "👤 Customer" if x == "customer"
                              else "🏦 Financial Institution",
        horizontal=True,
        key=f"account_type_badge_{tab_key}",
    )
    color = C.get("blue", "#2563EB") if selected == "institution" else C.get("teal", "#0D9488")
    label = "🏦 Financial Institution Portal" if selected == "institution" \
            else "👤 Customer Portal"
    st.markdown(
        f"<div style='padding:6px 14px;background:{color}15;border-radius:8px;"
        f"border:1px solid {color}30;font-size:0.78rem;color:{color};"
        f"font-weight:600;margin-bottom:12px'>"
        f"{label} — enter the email and password you registered with."
        f"</div>",
        unsafe_allow_html=True,
    )


def render() -> UserSession | None:
    """
    Renders the auth screen. Returns a UserSession if login/register
    just succeeded this run, otherwise None.
    """
    st.markdown(
        f"""
        <div style='text-align:center;padding:40px 0 20px 0'>
            <div style='font-size:3rem'>🏦</div>
            <div style='font-size:1.6rem;font-weight:800;color:{C["text"]}'>
                Credit Risk Intelligence Platform</div>
            <div style='font-size:0.9rem;color:{C["text3"]}'>
                Sign in to continue</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register, tab_forgot = st.tabs(
            ["🔑 Login", "✨ Create Account", "🔁 Forgot Password"]
        )
        with tab_login:
            result = _login_form()
            if result:
                return result
        with tab_register:
            result = _register_form()
            if result:
                return result
        with tab_forgot:
            _forgot_password_form()

    return None


def _login_form() -> UserSession | None:
    # Account type badge — shows which portal the user is accessing
    _account_type_badge("login")

    with st.form("login_form"):
        email    = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Login", type="primary", use_container_width=True
        )

    if submitted:
        if not email or not password:
            st.error("Please enter both email and password.")
            return None
        try:
            if _TRACING:
                with _ls_trace(
                    name="auth.login_attempt",
                    run_type="chain",
                    metadata={"component": "auth_ui", "step": "login", "email": email},
                ):
                    token, session = service.login(email, password)
            else:
                token, session = service.login(email, password)
            st.session_state["auth_token"]   = token
            st.session_state["user_session"] = session
            st.success(f"Welcome back, {session.full_name}!")
            st.rerun()
        except service.AuthError as exc:
            st.error(str(exc))
    return None


def _register_form() -> UserSession | None:
    with st.form("register_form"):
        full_name = st.text_input("Full Name", placeholder="Jane Doe")
        email     = st.text_input(
            "Email", placeholder="you@example.com", key="reg_email"
        )
        password  = st.text_input(
            "Password", type="password", key="reg_pw",
            help="Minimum 8 characters",
        )
        account_type = st.radio(
            "Account Type",
            options=[AccountType.CUSTOMER.value, AccountType.INSTITUTION.value],
            format_func=lambda x: "👤 Customer"
                                  if x == "customer"
                                  else "🏦 Financial Institution",
            horizontal=True,
        )
        institution_name = ""
        if account_type == AccountType.INSTITUTION.value:
            institution_name = st.text_input(
                "Institution Name", placeholder="e.g. HDFC Bank"
            )

        submitted = st.form_submit_button(
            "Create Account", type="primary", use_container_width=True
        )

    if submitted:
        if not full_name or not email or not password:
            st.error("Please fill in all required fields.")
            return None
        if len(password) < 8:
            st.error("Password must be at least 8 characters.")
            return None
        try:
            if _TRACING:
                with _ls_trace(
                    name="auth.register_attempt",
                    run_type="chain",
                    metadata={"component": "auth_ui", "step": "register",
                              "account_type": account_type},
                ):
                    token = service.register(
                        email, password, full_name, account_type,
                        institution_name or None,
                    )
                    _, session = service.login(email, password)
            else:
                token = service.register(
                    email, password, full_name, account_type,
                    institution_name or None,
                )
                _, session = service.login(email, password)
            st.session_state["auth_token"]   = token
            st.session_state["user_session"] = session
            st.success(f"Account created! Welcome, {full_name}.")
            st.info(
                "A verification email has been logged "
                "(check logs/dev_emails.log in dev mode)."
            )
            st.rerun()
        except service.AuthError as exc:
            st.error(str(exc))
    return None


def _forgot_password_form() -> None:
    # Account type badge — helps the user confirm which account they are resetting
    _account_type_badge("forgot")

    st.markdown(
        f"<p style='color:{C['text3']};font-size:0.85rem'>"
        f"Enter the email you registered with — a reset link will be generated.</p>",
        unsafe_allow_html=True,
    )
    with st.form("forgot_form"):
        email = st.text_input(
            "Email", placeholder="you@example.com", key="forgot_email"
        )
        submitted = st.form_submit_button(
            "Send Reset Link", use_container_width=True
        )

    if submitted and email:
        service.request_password_reset(email)
        st.success(
            "If an account exists with that email, a reset link has been "
            "generated. In dev mode (no SMTP configured), check "
            "logs/dev_emails.log for the reset token."
        )

    st.markdown("---")
    st.markdown(
        f"<p style='color:{C['text3']};font-size:0.8rem'>Have a reset token?</p>",
        unsafe_allow_html=True,
    )
    with st.form("reset_form"):
        token        = st.text_input("Reset Token", key="reset_token_input")
        new_password = st.text_input(
            "New Password", type="password", key="reset_new_pw"
        )
        submitted2 = st.form_submit_button(
            "Reset Password", use_container_width=True
        )

    if submitted2:
        if not token or not new_password:
            st.error("Please fill in both fields.")
        elif len(new_password) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            try:
                service.reset_password(token, new_password)
                st.success(
                    "Password reset successfully! "
                    "You can now log in with your new password."
                )
            except service.AuthError as exc:
                st.error(str(exc))
