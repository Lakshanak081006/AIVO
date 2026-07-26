from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import JSONType, TransportType, enum_column

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.travel import TravelPlan, TravelRequest
    from app.models.workflow import AgentMemory, ConfirmationRequest, SimulatedBooking


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(20), default="English", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    preference: Mapped["UserPreference | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    travel_requests: Mapped[list["TravelRequest"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    travel_plans: Mapped[list["TravelPlan"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    feedback_items: Mapped[list["Feedback"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    memories: Mapped[list["AgentMemory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["SimulatedBooking"]] = relationship(back_populates="user")
    confirmations: Mapped[list["ConfirmationRequest"]] = relationship(back_populates="user")


class UserPreference(TimestampMixin, Base):
    __tablename__ = "user_preferences"
    __table_args__ = (
        CheckConstraint(
            "minimum_hotel_rating IS NULL OR (minimum_hotel_rating >= 0 AND minimum_hotel_rating <= 5)",
            name="ck_user_preferences_hotel_rating",
        ),
        CheckConstraint(
            "maximum_hotel_distance IS NULL OR maximum_hotel_distance >= 0",
            name="ck_user_preferences_hotel_distance",
        ),
        CheckConstraint(
            "maximum_travel_duration IS NULL OR maximum_travel_duration > 0",
            name="ck_user_preferences_travel_duration",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    preferred_language: Mapped[str] = mapped_column(String(20), default="English", nullable=False)
    preferred_currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    preferred_transport_type: Mapped[TransportType | None] = mapped_column(
        enum_column(TransportType, "transport_type"), nullable=True
    )
    preferred_departure_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    maximum_travel_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_hotel_category: Mapped[str | None] = mapped_column(String(50))
    minimum_hotel_rating: Mapped[float | None] = mapped_column(Float)
    maximum_hotel_distance: Mapped[float | None] = mapped_column(Float)
    preferred_food_type: Mapped[str | None] = mapped_column(String(100))
    tourist_interests: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    avoid_early_morning: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avoid_late_night: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accessibility_requirements: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    pending_suggestions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONType, default=list, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="preference")
