from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import JSONType, TaskPriority, TaskStatus, enum_column

if TYPE_CHECKING:
    from app.models.travel import TravelPlan, TravelRequest
    from app.models.workflow import ActionLog


class AgentTask(TimestampMixin, Base):
    __tablename__ = "agent_tasks"
    __table_args__ = (
        CheckConstraint("weight > 0", name="ck_agent_tasks_weight_positive"),
        CheckConstraint("retry_count >= 0", name="ck_agent_tasks_retry_nonnegative"),
        CheckConstraint("maximum_retries >= 0", name="ck_agent_tasks_max_retry_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    travel_request_id: Mapped[int] = mapped_column(
        ForeignKey("travel_requests.id", ondelete="CASCADE"), index=True
    )
    travel_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True
    )
    task_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[TaskPriority] = mapped_column(
        enum_column(TaskPriority, "task_priority"), default=TaskPriority.MEDIUM, nullable=False
    )
    status: Mapped[TaskStatus] = mapped_column(
        enum_column(TaskStatus, "task_status"), default=TaskStatus.NOT_STARTED, nullable=False
    )
    can_run_in_parallel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    maximum_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    input_data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    output_data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    travel_request: Mapped["TravelRequest"] = relationship(back_populates="tasks")
    travel_plan: Mapped["TravelPlan | None"] = relationship(back_populates="tasks")
    dependencies: Mapped[list["TaskDependency"]] = relationship(
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    depended_on_by: Mapped[list["TaskDependency"]] = relationship(
        foreign_keys="TaskDependency.depends_on_task_id",
        back_populates="depends_on_task",
        cascade="all, delete-orphan",
    )
    action_logs: Mapped[list["ActionLog"]] = relationship(back_populates="agent_task")


class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        UniqueConstraint("task_id", "depends_on_task_id", name="uq_task_dependency_pair"),
        CheckConstraint("task_id <> depends_on_task_id", name="ck_task_dependency_not_self"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("agent_tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    depends_on_task_id: Mapped[int] = mapped_column(
        ForeignKey("agent_tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    task: Mapped["AgentTask"] = relationship(
        foreign_keys=[task_id], back_populates="dependencies"
    )
    depends_on_task: Mapped["AgentTask"] = relationship(
        foreign_keys=[depends_on_task_id], back_populates="depended_on_by"
    )
