from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import (
    ConfirmationStatus,
    JSONType,
    PlanStatus,
    WorkflowStatus,
    enum_column,
)

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.itinerary import BudgetBreakdown, ItineraryDay
    from app.models.option import Attraction, HotelOption, TransportOption, WeatherRecord
    from app.models.task import AgentTask
    from app.models.user import User
    from app.models.workflow import (
        ActionLog,
        ConfirmationRequest,
        ReplanningHistory,
        SimulatedBooking,
        WorkflowEvent,
    )


class TravelRequest(TimestampMixin, Base):
    __tablename__ = "travel_requests"
    __table_args__ = (
        CheckConstraint("traveller_count > 0", name="ck_travel_requests_travellers_positive"),
        CheckConstraint("budget >= 0", name="ck_travel_requests_budget_nonnegative"),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_travel_requests_date_order",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    original_instruction: Mapped[str] = mapped_column(Text, nullable=False)
    detected_language: Mapped[str | None] = mapped_column(String(20))
    response_language: Mapped[str] = mapped_column(String(20), default="English", nullable=False)
    source: Mapped[str | None] = mapped_column(String(120), index=True)
    destination: Mapped[str | None] = mapped_column(String(120), index=True)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    trip_duration_days: Mapped[int | None] = mapped_column(Integer)
    traveller_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    transport_preference: Mapped[str | None] = mapped_column(String(50))
    hotel_preference: Mapped[str | None] = mapped_column(String(100))
    minimum_hotel_rating: Mapped[float | None]
    food_preference: Mapped[str | None] = mapped_column(String(100))
    tourist_interests: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    special_requirements: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    extracted_requirements: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    missing_fields: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    clarification_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    clarification_question: Mapped[str | None] = mapped_column(Text)
    clarification_answer: Mapped[str | None] = mapped_column(Text)
    lyzr_session_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    workflow_status: Mapped[WorkflowStatus] = mapped_column(
        enum_column(WorkflowStatus, "workflow_status"),
        default=WorkflowStatus.CREATED,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="travel_requests")
    plans: Mapped[list["TravelPlan"]] = relationship(
        back_populates="travel_request", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["AgentTask"]] = relationship(back_populates="travel_request")
    action_logs: Mapped[list["ActionLog"]] = relationship(back_populates="travel_request")
    workflow_events: Mapped[list["WorkflowEvent"]] = relationship(back_populates="travel_request")


class TravelPlan(TimestampMixin, Base):
    __tablename__ = "travel_plans"
    __table_args__ = (
        CheckConstraint("total_cost >= 0", name="ck_travel_plans_total_nonnegative"),
        CheckConstraint("budget >= 0", name="ck_travel_plans_budget_nonnegative"),
        CheckConstraint("current_version > 0", name="ck_travel_plans_version_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    travel_request_id: Mapped[int] = mapped_column(
        ForeignKey("travel_requests.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[PlanStatus] = mapped_column(
        enum_column(PlanStatus, "plan_status"), default=PlanStatus.DRAFT, nullable=False
    )
    selected_transport_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "transport_options.id",
            name="fk_travel_plans_selected_transport",
            use_alter=True,
            ondelete="SET NULL",
        )
    )
    selected_hotel_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "hotel_options.id",
            name="fk_travel_plans_selected_hotel",
            use_alter=True,
            ondelete="SET NULL",
        )
    )
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    remaining_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    budget_exceeded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    final_summary: Mapped[str | None] = mapped_column(Text)
    confirmation_status: Mapped[ConfirmationStatus] = mapped_column(
        enum_column(ConfirmationStatus, "confirmation_status"),
        default=ConfirmationStatus.PENDING,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="travel_plans")
    travel_request: Mapped["TravelRequest"] = relationship(back_populates="plans")
    versions: Mapped[list["PlanVersion"]] = relationship(
        back_populates="travel_plan", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["AgentTask"]] = relationship(back_populates="travel_plan")
    transport_options: Mapped[list["TransportOption"]] = relationship(
        back_populates="travel_plan",
        foreign_keys="TransportOption.travel_plan_id",
        cascade="all, delete-orphan",
    )
    hotel_options: Mapped[list["HotelOption"]] = relationship(
        back_populates="travel_plan",
        foreign_keys="HotelOption.travel_plan_id",
        cascade="all, delete-orphan",
    )
    selected_transport: Mapped["TransportOption | None"] = relationship(
        foreign_keys=[selected_transport_id], post_update=True
    )
    selected_hotel: Mapped["HotelOption | None"] = relationship(
        foreign_keys=[selected_hotel_id], post_update=True
    )
    attractions: Mapped[list["Attraction"]] = relationship(
        back_populates="travel_plan", cascade="all, delete-orphan"
    )
    weather_records: Mapped[list["WeatherRecord"]] = relationship(
        back_populates="travel_plan", cascade="all, delete-orphan"
    )
    itinerary_days: Mapped[list["ItineraryDay"]] = relationship(
        back_populates="travel_plan", cascade="all, delete-orphan"
    )
    budget_breakdown: Mapped["BudgetBreakdown | None"] = relationship(
        back_populates="travel_plan", uselist=False, cascade="all, delete-orphan"
    )
    action_logs: Mapped[list["ActionLog"]] = relationship(
        back_populates="travel_plan", cascade="all, delete-orphan"
    )
    workflow_events: Mapped[list["WorkflowEvent"]] = relationship(
        back_populates="travel_plan", cascade="all, delete-orphan"
    )
    feedback_items: Mapped[list["Feedback"]] = relationship(
        back_populates="travel_plan", cascade="all, delete-orphan"
    )
    replanning_history: Mapped[list["ReplanningHistory"]] = relationship(
        back_populates="travel_plan", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["SimulatedBooking"]] = relationship(
        back_populates="travel_plan", cascade="all, delete-orphan"
    )
    confirmations: Mapped[list["ConfirmationRequest"]] = relationship(
        back_populates="travel_plan", cascade="all, delete-orphan"
    )


class PlanVersion(Base):
    __tablename__ = "plan_versions"
    __table_args__ = (
        UniqueConstraint("travel_plan_id", "version_number", name="uq_plan_version"),
        CheckConstraint("version_number > 0", name="ck_plan_versions_number_positive"),
        CheckConstraint("total_cost >= 0", name="ck_plan_versions_total_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_plan_id: Mapped[int] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    travel_plan: Mapped["TravelPlan"] = relationship(back_populates="versions")
