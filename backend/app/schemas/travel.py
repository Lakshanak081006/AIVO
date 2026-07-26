from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

class TravelPlanRequest(BaseModel):
    instruction: str = Field(min_length=5, max_length=2000)
    response_language: str = "English"

class ClarificationRequest(BaseModel):
    request_id: int
    answer: str = Field(min_length=1, max_length=1000)

class ReplanRequest(BaseModel):
    event_type: str
    reason: str | None = None
    payload: dict[str,Any] = Field(default_factory=dict)

class FeedbackRequest(BaseModel):
    overall_rating: int = Field(ge=1,le=5)
    transport_rating: int | None = Field(default=None,ge=1,le=5)
    hotel_rating: int | None = Field(default=None,ge=1,le=5)
    itinerary_rating: int | None = Field(default=None,ge=1,le=5)
    budget_rating: int | None = Field(default=None,ge=1,le=5)
    recommendation_rating: int | None = Field(default=None,ge=1,le=5)
    text_feedback: str | None = Field(default=None,max_length=3000)
    preference_tags: list[str] = Field(default_factory=list)

class ConfirmationAction(BaseModel):
    action_type: str = "BOOK_PLAN"
    decision: Literal["APPROVED","REJECTED"]
    description: str | None = None

class BookingRequest(BaseModel):
    booking_types: list[str] = Field(default_factory=lambda:["TRANSPORT","HOTEL"])

class DemoEventRequest(BaseModel):
    event_type: str
    mode: str | None = None
    payload: dict[str,Any] = Field(default_factory=dict)
