# src/auth/models.py
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class AccountType(str, Enum):
    CUSTOMER    = "customer"
    INSTITUTION = "institution"


class UserSession(BaseModel):
    """Represents the currently logged-in user. Stored in st.session_state."""
    email:             str
    full_name:         str
    account_type:      AccountType
    institution_name:  str | None = None
    is_authenticated:  bool = True


class RegisterRequest(BaseModel):
    email:            EmailStr
    password:         str = Field(min_length=8)
    full_name:        str = Field(min_length=2)
    account_type:     AccountType
    institution_name: str | None = None


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str
