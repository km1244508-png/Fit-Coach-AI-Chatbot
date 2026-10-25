"""Pydantic models for authentication."""
import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.timeutil import as_utc

PASSWORD_HINT = "Password must be 8-64 characters and include at least one letter and one number."


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("name")
    @classmethod
    def _clean_name(cls, v: str) -> str:
        v = re.sub(r"\s+", " ", v).strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        if not (8 <= len(v) <= 64) or len(v.encode("utf-8")) > 72:  # bcrypt limit is 72 bytes
            raise ValueError(PASSWORD_HINT)
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError(PASSWORD_HINT)
        return v

    @field_validator("confirm_password")
    @classmethod
    def _passwords_match(cls, v: str, info: Any) -> str:
        pw = info.data.get("password")
        if pw is not None and v != pw:
            raise ValueError("Passwords do not match")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    """Safe profile: never contains password / hash."""

    id: str
    name: str
    email: str
    created_at: datetime

    @classmethod
    def from_doc(cls, d: dict) -> "UserOut":
        return cls(id=str(d["_id"]), name=d["name"], email=d["email"], created_at=as_utc(d["created_at"]))


class AuthResponse(BaseModel):
    user: UserOut
    expires_in: int = Field(description="Session lifetime in seconds")


class MessageResponse(BaseModel):
    message: str
