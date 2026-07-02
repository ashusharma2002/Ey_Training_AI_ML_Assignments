# src/auth/database.py
# ============================================================
# SQLite-backed user store.
#
# Database path is environment-aware:
# - Local development: data/auth_db/users.db (relative)
# - Azure App Service: /home/data/auth_db/users.db
#   Azure mounts /home as PERSISTENT storage across deployments.
#   This means user accounts survive container restarts and
#   new deployments — accounts are never lost when you push code.
#   Requires WEBSITES_ENABLE_APP_SERVICE_STORAGE=true on Azure.
# ============================================================
from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone

# Use /home/data on Azure (persistent across deployments)
# Use local data/ folder for development
_AZURE_HOME = Path("/home")
if _AZURE_HOME.exists() and os.environ.get("WEBSITE_SITE_NAME"):
    # Running on Azure App Service — use persistent /home mount
    DB_PATH = _AZURE_HOME / "data" / "auth_db" / "users.db"
else:
    # Local development
    DB_PATH = Path("data/auth_db/users.db")


def _ensure_db_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    _ensure_db_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                email           TEXT UNIQUE NOT NULL,
                password_hash   TEXT NOT NULL,
                full_name       TEXT NOT NULL,
                account_type    TEXT NOT NULL CHECK(account_type IN ('customer', 'institution')),
                institution_name TEXT,
                is_verified     INTEGER NOT NULL DEFAULT 0,
                created_at      TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                email       TEXT NOT NULL,
                reset_token TEXT NOT NULL,
                expires_at  TEXT NOT NULL,
                used        INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_verifications (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                email       TEXT NOT NULL,
                verify_token TEXT NOT NULL,
                expires_at  TEXT NOT NULL,
                used        INTEGER NOT NULL DEFAULT 0
            )
        """)


def get_user_by_email(email: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
        return cur.fetchone()


def create_user(
    email: str,
    password_hash: str,
    full_name: str,
    account_type: str,
    institution_name: str | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO users (email, password_hash, full_name, account_type,
                                   institution_name, is_verified, created_at)
               VALUES (?, ?, ?, ?, ?, 0, ?)""",
            (
                email.lower().strip(), password_hash, full_name, account_type,
                institution_name, datetime.now(timezone.utc).isoformat(),
            ),
        )
        return cur.lastrowid


def mark_verified(email: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE users SET is_verified = 1 WHERE email = ?", (email.lower().strip(),))


def update_password(email: str, new_hash: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE email = ?", (new_hash, email.lower().strip()))


def store_reset_token(email: str, token: str, expires_at: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO password_resets (email, reset_token, expires_at, used) VALUES (?, ?, ?, 0)",
            (email.lower().strip(), token, expires_at),
        )


def get_valid_reset_token(token: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM password_resets WHERE reset_token = ? AND used = 0",
            (token,),
        )
        return cur.fetchone()


def consume_reset_token(token: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE password_resets SET used = 1 WHERE reset_token = ?", (token,))


def store_verification_token(email: str, token: str, expires_at: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO email_verifications (email, verify_token, expires_at, used) VALUES (?, ?, ?, 0)",
            (email.lower().strip(), token, expires_at),
        )


def get_valid_verification_token(token: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM email_verifications WHERE verify_token = ? AND used = 0",
            (token,),
        )
        return cur.fetchone()


def consume_verification_token(token: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE email_verifications SET used = 1 WHERE verify_token = ?", (token,))
