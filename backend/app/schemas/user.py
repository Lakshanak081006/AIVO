from __future__ import annotations

from datetime import datetime, time
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import TransportType
from app.schemas.auth import SUPPORTED_LANGUAGES, UserPublic


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    preferred_language: str | None = None

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("Full name must contain at least 2 characters")
        return normalized

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().title()
        if normalized not in SUPPORTED_LANGUAGES:
            raise ValueError("Supported languages are English, Tamil and Hindi")
        return normalized

    @model_validator(mode="after")
    def at_least_one(self):
        if self.full_name is None and self.preferred_language is None:
            raise ValueError("Provide at least one field to update")
        return self


class PreferenceUpdate(BaseModel):
    preferred_language: str | None = None
    preferred_currency: str | None = None
    preferred_transport_type: TransportType | None = None
    preferred_departure_time: time | None = None
    maximum_travel_duration: int | None = Field(default=None, gt=0, le=10080)
    preferred_hotel_category: str | None = Field(default=None, max_length=50)
    minimum_hotel_rating: float | None = Field(default=None, ge=0, le=5)
    maximum_hotel_distance: float | None = Field(default=None, ge=0, le=1000)
    preferred_food_type: str | None = Field(default=None, max_length=100)
    tourist_interests: list[str] | None = None
    avoid_early_morning: bool | None = None
    avoid_late_night: bool | None = None
    accessibility_requirements: list[str] | None = None

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().title()
        if normalized not in SUPPORTED_LANGUAGES:
            raise ValueError("Supported languages are English, Tamil and Hindi")
        return normalized

    @field_validator("preferred_currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("Currency must be a three-letter code")
        return normalized

    @field_validator("tourist_interests", "accessibility_requirements")
    @classmethod
    def normalize_lists(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            text = item.strip()
            key = text.lower()
            if text and key not in seen:
                cleaned.append(text[:100])
                seen.add(key)
        return cleaned

    @model_validator(mode="after")
    def at_least_one(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one preference to update")
        return self


class PreferenceResponse(BaseModel):
    id: int
    user_id: int
    preferred_language: str
    preferred_currency: str
    preferred_transport_type: TransportType | None
    preferred_departure_time: time | None
    maximum_travel_duration: int | None
    preferred_hotel_category: str | None
    minimum_hotel_rating: float | None
    maximum_hotel_distance: float | None
    preferred_food_type: str | None
    tourist_interests: list[str]
    avoid_early_morning: bool
    avoid_late_night: bool
    accessibility_requirements: list[str]
    pending_suggestions: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PreferenceDecision(BaseModel):
    suggestion_id: str = Field(min_length=1, max_length=100)
    decision: str

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        normalized = value.upper().strip()
        if normalized not in {"APPROVED", "REJECTED"}:
            raise ValueError("Decision must be APPROVED or REJECTED")
        return normalized


ProfileResponse = UserPublic
