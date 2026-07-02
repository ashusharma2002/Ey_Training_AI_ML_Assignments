# src/auth/service.py
# ============================================================
# Auth business logic: register, login, password reset, email
# verification. UI pages call ONLY this file, never database.py
# or security.py directly — this is the seam that lets you swap
# in Supabase/Auth0/Firebase later without touching the UI.
# ============================================================
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from src.auth import database as db
from src.auth.security import (
    hash_password, verify_password, create_session_token,
    generate_secure_token,
)
from src.auth.models import AccountType, UserSession
from src.utils.logger import get_logger
from config.settings import settings

try:
    from langsmith import traceable as _traceable
except ImportError:
    def _traceable(**kwargs):
        def decorator(func): return func
        return decorator

logger = get_logger(__name__)

_RESET_TOKEN_VALID_HOURS  = 1
_VERIFY_TOKEN_VALID_HOURS = 24


class AuthError(Exception):
    """Raised for any user-facing auth failure (bad password, duplicate email, etc.)."""


@_traceable(name="auth.register", run_type="chain", metadata={"component": "auth", "step": "register"})
def register(
    email: str,
    password: str,
    full_name: str,
    account_type: str,
    institution_name: str | None = None,
) -> str:
    """Returns a session JWT on success. Raises AuthError on failure."""
    db.init_db()
    existing = db.get_user_by_email(email)
    if existing:
        raise AuthError("An account with this email already exists. Try logging in instead.")

    if account_type == AccountType.INSTITUTION.value and not institution_name:
        raise AuthError("Institution name is required for Financial Institution accounts.")

    pw_hash = hash_password(password)
    db.create_user(email, pw_hash, full_name, account_type, institution_name)
    logger.info("New user registered: %s (%s)", email, account_type)

    _send_verification_email(email)

    return create_session_token(email, account_type, full_name)


@_traceable(name="auth.login", run_type="chain", metadata={"component": "auth", "step": "login"})
def login(email: str, password: str) -> tuple[str, UserSession]:
    """Returns (jwt_token, UserSession) on success. Raises AuthError on failure."""
    db.init_db()
    user = db.get_user_by_email(email)
    if not user:
        raise AuthError("No account found with this email. Check the email or create an account.")

    if not verify_password(password, user["password_hash"]):
        raise AuthError("Incorrect password. Try again or use 'Forgot Password'.")

    token = create_session_token(email, user["account_type"], user["full_name"])
    session = UserSession(
        email=user["email"],
        full_name=user["full_name"],
        account_type=AccountType(user["account_type"]),
        institution_name=user["institution_name"],
    )
    logger.info("Login successful: %s", email)
    return token, session


def request_password_reset(email: str) -> None:
    """Generates a reset token and 'sends' it (logs/saves it if no SMTP configured)."""
    db.init_db()
    user = db.get_user_by_email(email)
    if not user:
        # Deliberately don't reveal whether the email exists (standard
        # security practice — prevents account enumeration).
        logger.info("Password reset requested for unknown email: %s", email)
        return

    token = generate_secure_token()
    expires = (datetime.now(timezone.utc) + timedelta(hours=_RESET_TOKEN_VALID_HOURS)).isoformat()
    db.store_reset_token(email, token, expires)
    _send_reset_email(email, token)


def reset_password(token: str, new_password: str) -> None:
    db.init_db()
    row = db.get_valid_reset_token(token)
    if not row:
        raise AuthError("This reset link is invalid or has already been used.")

    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        raise AuthError("This reset link has expired. Please request a new one.")

    new_hash = hash_password(new_password)
    db.update_password(row["email"], new_hash)
    db.consume_reset_token(token)
    logger.info("Password reset completed for: %s", row["email"])


def verify_email(token: str) -> None:
    db.init_db()
    row = db.get_valid_verification_token(token)
    if not row:
        raise AuthError("This verification link is invalid or has already been used.")

    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        raise AuthError("This verification link has expired.")

    db.mark_verified(row["email"])
    db.consume_verification_token(token)


def _send_verification_email(email: str) -> None:
    token = generate_secure_token()
    expires = (datetime.now(timezone.utc) + timedelta(hours=_VERIFY_TOKEN_VALID_HOURS)).isoformat()
    db.store_verification_token(email, token, expires)
    _send_email(
        to=email,
        subject="Verify your Credit Risk Intelligence Platform account",
        body=f"Welcome! Your verification code/link: {token}\n\n"
             f"(In production, this would be a clickable link to your domain "
             f"e.g. https://yourapp.com/verify?token={token})",
    )


def _send_reset_email(email: str, token: str) -> None:
    _send_email(
        to=email,
        subject="Reset your password",
        body=f"Your password reset code/link: {token}\n\n"
             f"This expires in {_RESET_TOKEN_VALID_HOURS} hour(s).\n"
             f"(In production, this would be a clickable link e.g. "
             f"https://yourapp.com/reset-password?token={token})",
    )


def _send_email(to: str, subject: str, body: str) -> None:
    """
    Sends an email via SMTP if configured in .env, otherwise safely
    logs it to console + a local file — so the auth flow never crashes
    and you can still test reset/verification locally without a real
    email account configured.
    """
    if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            import smtplib
            from email.mime.text import MIMEText

            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"]    = settings.SMTP_USER
            msg["To"]      = to

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info("Email sent to %s: %s", to, subject)
            return
        except Exception as exc:
            logger.error("SMTP send failed (%s) — falling back to console log.", exc)

    # Fallback: no SMTP configured, or SMTP failed — log instead of crashing.
    logger.info("=== EMAIL (not sent — no SMTP configured) ===")
    logger.info("To: %s | Subject: %s", to, subject)
    logger.info("Body: %s", body)
    try:
        from pathlib import Path
        log_file = Path("logs/dev_emails.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"\n--- {datetime.now(timezone.utc).isoformat()} ---\n")
            f.write(f"To: {to}\nSubject: {subject}\n{body}\n")
    except Exception:
        pass
