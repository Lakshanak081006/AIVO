from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
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
    ActionLogStatus,
    BookingStatus,
    ConfirmationStatus,
    JSONType,
    enum_column,
)

if TYPE_CHECKING:
    from app.models.task import AgentTask
    from app.models.travel import TravelPlan, TravelRequest
    from app.models.user import User


class ActionLog(Base):
    __tablename__ = "action_logs"
    __table_args__ = (
        CheckConstraint("retry_count >= 0", name="ck_action_logs_retry_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("travel_requests.id", ondelete="CASCADE"), index=True
    )
    travel_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True
    )
    agent_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("agent_tasks.id", ondelete="SET NULL"), index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
    agent_name: Mapped[str | None] = mapped_column(String(100), index=True)
    task_name: Mapped[str | None] = mapped_column(String(150), index=True)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    action_performed: Mapped[str] = mapped_column(Text, nullable=False)
    tool_used: Mapped[str | None] = mapped_column(String(120))
    input_summary: Mapped[str | None] = mapped_column(Text)
    output_summary: Mapped[str | None] = mapped_column(Text)
    decision: Mapped[str | None] = mapped_column(Text)
    decision_reason: Mapped[str | None] = mapped_column(Text)
    error_details: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[ActionLogStatus] = mapped_column(
        enum_column(ActionLogStatus, "action_log_status"),
        default=ActionLogStatus.INFO,
        nullable=False,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    travel_request: Mapped["TravelRequest | None"] = relationship(back_populates="action_logs")
    travel_plan: Mapped["TravelPlan | None"] = relationship(back_populates="action_logs")
    agent_task: Mapped["AgentTask | None"] = relationship(back_populates="action_logs")


class AgentMemory(TimestampMixin, Base):
    __tablename__ = "agent_memory"
    __table_args__ = (
        UniqueConstraint("user_id", "memory_key", name="uq_agent_memory_user_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    memory_key: Mapped[str] = mapped_column(String(150), nullable=False)
    memory_value: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    approved: Mapped[bool] = mapped_column(default=False, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100))

    user: Mapped["User"] = relationship(back_populates="memories")


class ReplanningHistory(Base):
    __tablename__ = "replanning_history"
    __table_args__ = (
        CheckConstraint("previous_version > 0", name="ck_replanning_previous_positive"),
        CheckConstraint("new_version > previous_version", name="ck_replanning_version_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_plan_id: Mapped[int] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True
    )
    previous_version: Mapped[int] = mapped_column(Integer, nullable=False)
    new_version: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    triggering_event: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    affected_tasks: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    preserved_tasks: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    old_selection: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    new_selection: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    old_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    new_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    cost_difference: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    travel_plan: Mapped["TravelPlan"] = relationship(back_populates="replanning_history")


class SimulatedBooking(TimestampMixin, Base):
    __tablename__ = "simulated_bookings"
    __table_args__ = (CheckConstraint("amount >= 0", name="ck_booking_amount_nonnegative"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_plan_id: Mapped[int] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    booking_reference: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    booking_type: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    selected_option_id: Mapped[int | None] = mapped_column(Integer)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        enum_column(BookingStatus, "booking_status"), default=BookingStatus.PENDING, nullable=False
    )
    confirmation_status: Mapped[ConfirmationStatus] = mapped_column(
        enum_column(ConfirmationStatus, "confirmation_status"),
        default=ConfirmationStatus.PENDING,
        nullable=False,
    )
    booking_details: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    travel_plan: Mapped["TravelPlan"] = relationship(back_populates="bookings")
    user: Mapped["User"] = relationship(back_populates="bookings")


class ConfirmationRequest(Base):
    __tablename__ = "confirmation_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_plan_id: Mapped[int] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    status: Mapped[ConfirmationStatus] = mapped_column(
        enum_column(ConfirmationStatus, "confirmation_status"),
        default=ConfirmationStatus.PENDING,
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    travel_plan: Mapped["TravelPlan"] = relationship(back_populates="confirmations")
    user: Mapped["User"] = relationship(back_populates="confirmations")


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"
    __table_args__ = (
        CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="ck_workflow_event_progress",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("travel_requests.id", ondelete="CASCADE"), index=True
    )
    travel_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    agent_name: Mapped[str | None] = mapped_column(String(100))
    task_name: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    event_data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    travel_request: Mapped["TravelRequest | None"] = relationship(back_populates="workflow_events")
    travel_plan: Mapped["TravelPlan | None"] = relationship(back_populates="workflow_events")
