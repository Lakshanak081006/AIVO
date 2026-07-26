from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.feedback import Feedback
from app.models.itinerary import BudgetBreakdown
from app.models.task import AgentTask
from app.models.travel import TravelPlan, TravelRequest
from app.models.user import User
from app.models.workflow import WorkflowEvent


def create_user(db_session) -> User:
    user = User(
        full_name="Test User",
        email=f"{uuid4()}@example.com",
        password_hash="hashed-value",
        preferred_language="English",
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_request_and_plan(db_session):
    user = create_user(db_session)
    request = TravelRequest(
        user_id=user.id,
        original_instruction="Plan a test trip",
        source="Coimbatore",
        destination="Chennai",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 2),
        traveller_count=2,
        budget=Decimal("20000"),
    )
    db_session.add(request)
    db_session.flush()
    plan = TravelPlan(
        user_id=user.id,
        travel_request_id=request.id,
        title="Test Trip",
        budget=Decimal("20000"),
    )
    db_session.add(plan)
    db_session.flush()
    return user, request, plan


def test_user_creation(db_session):
    user = create_user(db_session)
    assert user.id is not None
    assert user.is_active is True


def test_invalid_travel_request_traveller_count(db_session):
    user = create_user(db_session)
    db_session.add(
        TravelRequest(
            user_id=user.id,
            original_instruction="Invalid trip",
            traveller_count=0,
            budget=Decimal("100"),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_agent_task_creation(db_session):
    _, request, plan = create_request_and_plan(db_session)
    task = AgentTask(
        task_uuid=str(uuid4()),
        travel_request_id=request.id,
        travel_plan_id=plan.id,
        task_name="Validate requirements",
        agent_name="PlannerAgent",
        weight=2,
    )
    db_session.add(task)
    db_session.flush()
    assert task.id is not None
    assert task.retry_count == 0


def test_negative_budget_rejected(db_session):
    _, _, plan = create_request_and_plan(db_session)
    db_session.add(
        BudgetBreakdown(
            travel_plan_id=plan.id,
            transport_cost=Decimal("-1"),
            user_budget=Decimal("100"),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_feedback_rating_constraint(db_session):
    user, _, plan = create_request_and_plan(db_session)
    db_session.add(
        Feedback(user_id=user.id, travel_plan_id=plan.id, overall_rating=6)
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_workflow_progress_constraint(db_session):
    _, request, plan = create_request_and_plan(db_session)
    db_session.add(
        WorkflowEvent(
            travel_request_id=request.id,
            travel_plan_id=plan.id,
            event_type="TEST",
            status="RUNNING",
            progress_percentage=101,
            message="Invalid progress",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
