from __future__ import annotations

from enum import Enum

from sqlalchemy import Enum as SAEnum, JSON
from sqlalchemy.dialects.postgresql import JSONB

JSONType = JSON().with_variant(JSONB, "postgresql")


def enum_column(enum_class: type[Enum], name: str) -> SAEnum:
    return SAEnum(
        enum_class,
        name=name,
        values_callable=lambda enum: [item.value for item in enum],
        native_enum=False,
        validate_strings=True,
    )


class TaskPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    WAITING = "WAITING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class WorkflowStatus(str, Enum):
    CREATED = "CREATED"
    WAITING_FOR_CLARIFICATION = "WAITING_FOR_CLARIFICATION"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    REPLANNING = "REPLANNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ConfirmationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class TransportType(str, Enum):
    TRAIN = "TRAIN"
    BUS = "BUS"
    FLIGHT = "FLIGHT"
    CAR = "CAR"
    LOCAL_TRANSPORT = "LOCAL_TRANSPORT"


class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    GENERATING = "GENERATING"
    READY = "READY"
    CONFIRMED = "CONFIRMED"
    BOOKED = "BOOKED"
    REPLANNING = "REPLANNING"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class ActionLogStatus(str, Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    RETRY = "RETRY"


class PreferenceSuggestionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
