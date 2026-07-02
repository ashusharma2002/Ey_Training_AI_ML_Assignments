# tests/unit/test_auth.py
# Covers Phase 6 — Authentication System
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

# Use an isolated test database so these tests never touch the real one
os.environ.setdefault("AUTH_TEST_MODE", "1")


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Each test gets its own throwaway SQLite file."""
    from src.auth import database as db
    test_db_path = tmp_path / "test_users.db"
    monkeypatch.setattr(db, "DB_PATH", test_db_path)
    db.init_db()
    yield


def test_password_hashing_roundtrip():
    from src.auth.security import hash_password, verify_password
    h = hash_password("MySecurePass123")
    assert h != "MySecurePass123"  # never stored in plaintext
    assert verify_password("MySecurePass123", h) is True
    assert verify_password("WrongPassword", h) is False


def test_jwt_create_and_decode():
    from src.auth.security import create_session_token, decode_session_token
    token = create_session_token("test@example.com", "customer", "Test User")
    decoded = decode_session_token(token)
    assert decoded["email"] == "test@example.com"
    assert decoded["account_type"] == "customer"


def test_jwt_invalid_token_returns_none():
    from src.auth.security import decode_session_token
    assert decode_session_token("not.a.valid.jwt") is None


def test_register_new_customer_succeeds():
    from src.auth import service
    token = service.register("alice@example.com", "Password123", "Alice", "customer")
    assert isinstance(token, str) and len(token) > 20


def test_register_duplicate_email_raises():
    from src.auth import service
    service.register("bob@example.com", "Password123", "Bob", "customer")
    with pytest.raises(service.AuthError):
        service.register("bob@example.com", "AnotherPass1", "Bob Two", "customer")


def test_register_institution_requires_name():
    from src.auth import service
    with pytest.raises(service.AuthError):
        service.register("hr@bank.com", "Password123", "HR Officer", "institution")


def test_register_institution_with_name_succeeds():
    from src.auth import service
    token = service.register("hr2@bank.com", "Password123", "HR Officer", "institution", "Test Bank")
    assert isinstance(token, str)


def test_login_correct_credentials():
    from src.auth import service
    service.register("carol@example.com", "Password123", "Carol", "customer")
    token, session = service.login("carol@example.com", "Password123")
    assert session.email == "carol@example.com"
    assert session.account_type.value == "customer"


def test_login_wrong_password_raises():
    from src.auth import service
    service.register("dave@example.com", "Password123", "Dave", "customer")
    with pytest.raises(service.AuthError):
        service.login("dave@example.com", "WrongPassword")


def test_login_nonexistent_email_raises():
    from src.auth import service
    with pytest.raises(service.AuthError):
        service.login("nobody@example.com", "Password123")


def test_password_reset_flow():
    from src.auth import service, database as db
    service.register("eve@example.com", "OldPassword1", "Eve", "customer")
    service.request_password_reset("eve@example.com")

    # Fetch the token directly from DB (simulating clicking the emailed link)
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT reset_token FROM password_resets WHERE email = ? ORDER BY id DESC LIMIT 1",
            ("eve@example.com",),
        ).fetchone()
    token = row["reset_token"]

    service.reset_password(token, "NewPassword123")
    # Old password should no longer work
    with pytest.raises(service.AuthError):
        service.login("eve@example.com", "OldPassword1")
    # New password should work
    _, session = service.login("eve@example.com", "NewPassword123")
    assert session.email == "eve@example.com"


def test_password_reset_token_cannot_be_reused():
    from src.auth import service, database as db
    service.register("frank@example.com", "Password123", "Frank", "customer")
    service.request_password_reset("frank@example.com")
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT reset_token FROM password_resets WHERE email = ? ORDER BY id DESC LIMIT 1",
            ("frank@example.com",),
        ).fetchone()
    token = row["reset_token"]
    service.reset_password(token, "NewPassword1")
    with pytest.raises(service.AuthError):
        service.reset_password(token, "AnotherPassword2")


def test_request_reset_for_unknown_email_does_not_raise():
    """Security best practice: don't reveal whether an email is registered."""
    from src.auth import service
    service.request_password_reset("unknown@example.com")  # should not raise
