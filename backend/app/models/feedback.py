from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import JSONType

if TYPE_CHECKING:
    from app.models.travel import TravelPlan
    from app.models.user import User


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint("overall_rating BETWEEN 1 AND 5", name="ck_feedback_overall_rating"),
        CheckConstraint("transport_rating IS NULL OR transport_rating BETWEEN 1 AND 5", name="ck_feedback_transport_rating"),
        CheckConstraint("hotel_rating IS NULL OR hotel_rating BETWEEN 1 AND 5", name="ck_feedback_hotel_rating"),
        CheckConstraint("itinerary_rating IS NULL OR itinerary_rating BETWEEN 1 AND 5", name="ck_feedback_itinerary_rating"),
        CheckConstraint("budget_rating IS NULL OR budget_rating BETWEEN 1 AND 5", name="ck_feedback_budget_rating"),
        CheckConstraint("recommendation_rating IS NULL OR recommendation_rating BETWEEN 1 AND 5", name="ck_feedback_recommendation_rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    travel_plan_id: Mapped[int] = mapped_column(ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    transport_rating: Mapped[int | None] = mapped_column(Integer)
    hotel_rating: Mapped[int | None] = mapped_column(Integer)
    itinerary_rating: Mapped[int | None] = mapped_column(Integer)
    budget_rating: Mapped[int | None] = mapped_column(Integer)
    recommendation_rating: Mapped[int | None] = mapped_column(Integer)
    text_feedback: Mapped[str | None] = mapped_column(Text)
    preference_tags: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="feedback_items")
    travel_plan: Mapped["TravelPlan"] = relationship(back_populates="feedback_items")
