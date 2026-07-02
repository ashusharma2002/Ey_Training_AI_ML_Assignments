# src/auth/security.py
# ============================================================
# Password hashing (bcrypt) and session tokens (JWT).
# ============================================================
from __future__ import annotations
import secrets
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from config.settings import settings

_JWT_ALGO = "HS256"


def hash_password(plain_password: str) -> str:
    """Bcrypt hash — includes its own salt, safe to store directly."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_session_token(email: str, account_type: str, full_name: str) -> str:
    """JWT session token — stored in Streamlit session_state, not a cookie,
    since Streamlit doesn't have first-class cookie support. This still
    gives proper expiry and tamper-proof claims."""
    payload = {
        "email": email,
        "account_type": account_type,
        "full_name": full_name,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=_JWT_ALGO)


def decode_session_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[_JWT_ALGO])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_secure_token() -> str:
    """For password-reset and email-verification links."""
    return secrets.token_urlsafe(32)
