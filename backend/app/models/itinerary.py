from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Time, UniqueConstraint
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.travel import TravelPlan


class ItineraryDay(Base):
    __tablename__ = "itinerary_days"
    __table_args__ = (
        UniqueConstraint("travel_plan_id", "day_number", name="uq_itinerary_day_number"),
        CheckConstraint("day_number > 0", name="ck_itinerary_day_positive"),
        CheckConstraint("estimated_daily_cost >= 0", name="ck_itinerary_daily_cost_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_plan_id: Mapped[int] = mapped_column(ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    itinerary_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str | None] = mapped_column(String(180))
    estimated_daily_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    travel_plan: Mapped["TravelPlan"] = relationship(back_populates="itinerary_days")
    activities: Mapped[list["ItineraryActivity"]] = relationship(
        back_populates="itinerary_day", cascade="all, delete-orphan", order_by="ItineraryActivity.display_order"
    )


class ItineraryActivity(Base):
    __tablename__ = "itinerary_activities"
    __table_args__ = (
        CheckConstraint("travel_time_minutes >= 0", name="ck_activity_travel_time_nonnegative"),
        CheckConstraint("estimated_cost >= 0", name="ck_activity_cost_nonnegative"),
        CheckConstraint("display_order >= 0", name="ck_activity_display_order_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    itinerary_day_id: Mapped[int] = mapped_column(
        ForeignKey("itinerary_days.id", ondelete="CASCADE"), index=True
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    activity: Mapped[str] = mapped_column(String(180), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    environment_type: Mapped[str] = mapped_column(String(20), default="mixed", nullable=False)
    travel_time_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"), nullable=False)
    weather_suitability: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    itinerary_day: Mapped["ItineraryDay"] = relationship(back_populates="activities")


class BudgetBreakdown(TimestampMixin, Base):
    __tablename__ = "budget_breakdowns"
    __table_args__ = (
        CheckConstraint("transport_cost >= 0", name="ck_budget_transport_nonnegative"),
        CheckConstraint("hotel_cost >= 0", name="ck_budget_hotel_nonnegative"),
        CheckConstraint("food_cost >= 0", name="ck_budget_food_nonnegative"),
        CheckConstraint("local_transport_cost >= 0", name="ck_budget_local_nonnegative"),
        CheckConstraint("attraction_cost >= 0", name="ck_budget_attraction_nonnegative"),
        CheckConstraint("taxes >= 0", name="ck_budget_taxes_nonnegative"),
        CheckConstraint("emergency_reserve >= 0", name="ck_budget_reserve_nonnegative"),
        CheckConstraint("other_expenses >= 0", name="ck_budget_other_nonnegative"),
        CheckConstraint("total_cost >= 0", name="ck_budget_total_nonnegative"),
        CheckConstraint("user_budget >= 0", name="ck_budget_user_nonnegative"),
        CheckConstraint("exceeded_amount >= 0", name="ck_budget_exceeded_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_plan_id: Mapped[int] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), unique=True, index=True
    )
    transport_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    hotel_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    food_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    local_transport_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    attraction_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    taxes: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    emergency_reserve: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    other_expenses: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    user_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    remaining_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    exceeded_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    within_budget: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    travel_plan: Mapped["TravelPlan"] = relationship(back_populates="budget_breakdown")
