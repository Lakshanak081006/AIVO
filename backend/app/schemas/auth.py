from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

SUPPORTED_LANGUAGES = {"English", "Tamil", "Hindi"}


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    preferred_language: str = "English"

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("Full name must contain at least 2 characters")
        return normalized

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        rules = [r"[A-Z]", r"[a-z]", r"\d", r"[^A-Za-z0-9]"]
        if not all(re.search(rule, value) for rule in rules):
            raise ValueError(
                "Password must include uppercase, lowercase, number and special character"
            )
        return value

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        normalized = value.strip().title()
        if normalized not in SUPPORTED_LANGUAGES:
            raise ValueError("Supported languages are English, Tamil and Hindi")
        return normalized


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserPublic(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    preferred_language: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: datetime
    user: UserPublic
