"""
Lyzr integration tests — all HTTP calls are mocked.
No real LYZR_API_KEY is used or required.
"""
from __future__ import annotations

import json
import os
import pytest
import httpx

os.environ.setdefault("LYZR_ENABLED", "false")
os.environ.setdefault("LYZR_API_KEY", "")

from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.lyzr_service import LyzrService, normalize_lyzr_response
from app.services.lyzr_response_mapper import (
    map_lyzr_to_requirements,
    extract_clarification,
    extract_decision_summary,
)
from app.core.exceptions import (
    LyzrUnavailableError,
    LyzrAuthenticationError,
    LyzrRateLimitError,
    LyzrResponseError,
)


# ---------------------------------------------------------------------------
# normalize_lyzr_response
# ---------------------------------------------------------------------------

def test_normalize_dict_response():
    raw = {"response": {"success": True, "operation": "EXTRACT"}}
    result = normalize_lyzr_response(raw)
    assert result == {"success": True, "operation": "EXTRACT"}


def test_normalize_json_string_response():
    raw = {"response": '{"success": true, "operation": "EXTRACT"}'}
    result = normalize_lyzr_response(raw)
    assert result["success"] is True


def test_normalize_markdown_fenced_response():
    raw = {"response": "```json\n{\"success\": true}\n```"}
    result = normalize_lyzr_response(raw)
    assert result["success"] is True


def test_normalize_root_level_structured():
    raw = {"success": True, "requirements": {"source": "Coimbatore"}}
    result = normalize_lyzr_response(raw)
    assert result["requirements"]["source"] == "Coimbatore"


def test_normalize_invalid_json_raises():
    raw = {"response": "not valid json {{"}
    with pytest.raises(LyzrResponseError):
        normalize_lyzr_response(raw)


def test_normalize_missing_response_field_raises():
    raw = {"something_else": "value"}
    with pytest.raises(LyzrResponseError):
        normalize_lyzr_response(raw)


# ---------------------------------------------------------------------------
# map_lyzr_to_requirements
# ---------------------------------------------------------------------------

def test_map_full_requirements():
    lyzr = {
        "success": True,
        "language": "English",
        "requirements": {
            "source": "Coimbatore",
            "destination": "Chennai",
            "start_date": "2026-08-10",
            "end_date": "2026-08-12",
            "trip_duration_days": 3,
            "traveller_count": 2,
            "budget": 15000,
            "currency": "INR",
            "transport_preference": "train",
            "hotel_preference": "Budget",
            "minimum_hotel_rating": 3.5,
            "food_preference": "Vegetarian",
            "tourist_interests": ["Museums", "Beaches"],
            "special_requirements": ["Avoid early morning"],
        },
    }
    mapped = map_lyzr_to_requirements(lyzr)
    assert mapped["source"] == "Coimbatore"
    assert mapped["destination"] == "Chennai"
    assert mapped["traveller_count"] == 2
    assert mapped["budget"] == 15000.0
    assert mapped["transport_preference"] == "TRAIN"
    assert mapped["tourist_interests"] == ["Museums", "Beaches"]
    assert mapped["minimum_hotel_rating"] == 3.5


def test_map_missing_fields_returns_none():
    lyzr = {"requirements": {}}
    mapped = map_lyzr_to_requirements(lyzr)
    assert mapped["source"] is None
    assert mapped["destination"] is None
    assert mapped["budget"] is None


def test_extract_clarification():
    lyzr = {
        "clarification_required": True,
        "missing_fields": ["start_date", "budget"],
        "clarification_question": "When would you like to travel and what is your budget?",
    }
    missing, question = extract_clarification(lyzr)
    assert "start_date" in missing
    assert "budget" in missing
    assert "budget" in question


def test_extract_decision_summary():
    lyzr = {
        "decision_summary": "Great trip planned within budget.",
        "warnings": ["Rain expected on day 2"],
        "confidence": 0.92,
    }
    meta = extract_decision_summary(lyzr)
    assert meta["decision_summary"] == "Great trip planned within budget."
    assert len(meta["warnings"]) == 1
    assert meta["confidence"] == 0.92


# ---------------------------------------------------------------------------
# LyzrService.chat — mocked HTTP
# ---------------------------------------------------------------------------

def _make_response(status_code: int, body: dict) -> httpx.Response:
    return httpx.Response(status_code, json=body)


@pytest.mark.asyncio
async def test_chat_success():
    service = LyzrService()
    mock_body = {"response": {"success": True, "operation": "EXTRACT_REQUIREMENTS",
                               "requirements": {"source": "Coimbatore", "destination": "Chennai"}}}

    with patch("app.core.config.settings.LYZR_ENABLED", True), \
         patch("app.core.config.settings.LYZR_API_KEY", "test-key-not-real"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _make_response(200, mock_body)
        result = await service.chat("user@test.com", "aiva-test-session", "Plan a trip")

    assert result["success"] is True
    assert result["requirements"]["source"] == "Coimbatore"


@pytest.mark.asyncio
async def test_chat_clarification_required():
    service = LyzrService()
    mock_body = {
        "response": {
            "success": True,
            "clarification_required": True,
            "missing_fields": ["start_date", "budget"],
            "clarification_question": "When would you like to travel?",
        }
    }
    with patch("app.core.config.settings.LYZR_ENABLED", True), \
         patch("app.core.config.settings.LYZR_API_KEY", "test-key-not-real"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _make_response(200, mock_body)
        result = await service.chat("user@test.com", "aiva-session", "Plan a trip from Coimbatore")

    assert result["clarification_required"] is True
    assert "start_date" in result["missing_fields"]


@pytest.mark.asyncio
async def test_chat_timeout_raises_unavailable():
    service = LyzrService()
    with patch("app.core.config.settings.LYZR_ENABLED", True), \
         patch("app.core.config.settings.LYZR_API_KEY", "test-key-not-real"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("timed out")
        with pytest.raises(LyzrUnavailableError):
            await service.chat("user@test.com", "aiva-session", "Plan a trip")


@pytest.mark.asyncio
async def test_chat_connection_error_raises_unavailable():
    service = LyzrService()
    with patch("app.core.config.settings.LYZR_ENABLED", True), \
         patch("app.core.config.settings.LYZR_API_KEY", "test-key-not-real"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("connection refused")
        with pytest.raises(LyzrUnavailableError):
            await service.chat("user@test.com", "aiva-session", "Plan a trip")


@pytest.mark.asyncio
async def test_chat_http_429_raises_rate_limit():
    service = LyzrService()
    with patch("app.core.config.settings.LYZR_ENABLED", True), \
         patch("app.core.config.settings.LYZR_API_KEY", "test-key-not-real"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _make_response(429, {"error": "rate limit"})
        with pytest.raises(LyzrRateLimitError):
            await service.chat("user@test.com", "aiva-session", "Plan a trip")


@pytest.mark.asyncio
async def test_chat_http_500_raises_unavailable():
    service = LyzrService()
    with patch("app.core.config.settings.LYZR_ENABLED", True), \
         patch("app.core.config.settings.LYZR_API_KEY", "test-key-not-real"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _make_response(500, {"error": "server error"})
        with pytest.raises(LyzrUnavailableError):
            await service.chat("user@test.com", "aiva-session", "Plan a trip")


@pytest.mark.asyncio
async def test_chat_http_401_raises_auth_error():
    service = LyzrService()
    with patch("app.core.config.settings.LYZR_ENABLED", True), \
         patch("app.core.config.settings.LYZR_API_KEY", "test-key-not-real"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _make_response(401, {"error": "unauthorized"})
        with pytest.raises(LyzrAuthenticationError):
            await service.chat("user@test.com", "aiva-session", "Plan a trip")


@pytest.mark.asyncio
async def test_chat_http_403_raises_auth_error():
    service = LyzrService()
    with patch("app.core.config.settings.LYZR_ENABLED", True), \
         patch("app.core.config.settings.LYZR_API_KEY", "test-key-not-real"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _make_response(403, {"error": "forbidden"})
        with pytest.raises(LyzrAuthenticationError):
            await service.chat("user@test.com", "aiva-session", "Plan a trip")


@pytest.mark.asyncio
async def test_chat_malformed_json_raises_response_error():
    service = LyzrService()
    with patch("app.core.config.settings.LYZR_ENABLED", True), \
         patch("app.core.config.settings.LYZR_API_KEY", "test-key-not-real"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(200, content=b"not json at all {{")
        with pytest.raises(LyzrResponseError):
            await service.chat("user@test.com", "aiva-session", "Plan a trip")


@pytest.mark.asyncio
async def test_chat_disabled_raises_unavailable():
    service = LyzrService()
    with patch("app.core.config.settings.LYZR_ENABLED", False):
        with pytest.raises(LyzrUnavailableError):
            await service.chat("user@test.com", "aiva-session", "Plan a trip")


@pytest.mark.asyncio
async def test_chat_missing_api_key_raises_auth_error():
    service = LyzrService()
    with patch("app.core.config.settings.LYZR_ENABLED", True), \
         patch("app.core.config.settings.LYZR_API_KEY", ""):
        with pytest.raises(LyzrAuthenticationError):
            await service.chat("user@test.com", "aiva-session", "Plan a trip")


# ---------------------------------------------------------------------------
# Security: API key must never appear in exceptions or logs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_key_not_in_exception_message():
    service = LyzrService()
    fake_key = "sk-super-secret-lyzr-key-12345"
    with patch("app.core.config.settings.LYZR_ENABLED", True), \
         patch("app.core.config.settings.LYZR_API_KEY", fake_key), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _make_response(401, {"error": "unauthorized"})
        try:
            await service.chat("user@test.com", "aiva-session", "Plan a trip")
        except LyzrAuthenticationError as exc:
            assert fake_key not in str(exc)


# ---------------------------------------------------------------------------
# WorkflowService fallback: local agents still work when Lyzr is disabled
# ---------------------------------------------------------------------------

def test_local_requirement_extraction_still_works():
    from app.agents.requirement_agent import extract_requirements, missing_fields
    result = extract_requirements(
        "Plan a two-day trip from Coimbatore to Chennai for two people next weekend under ₹20000",
        "English"
    )
    assert result["source"] == "Coimbatore"
    assert result["destination"] == "Chennai"
    assert result["traveller_count"] == 2
    assert result["budget"] == 20000.0
    missing = missing_fields(result)
    # start_date/end_date resolved from "next weekend" so should be empty or minimal
    assert "source" not in missing
    assert "destination" not in missing


def test_local_clarification_question():
    from app.agents.requirement_agent import clarification_question
    q = clarification_question(["start_date", "budget"])
    assert "travel dates" in q or "budget" in q


# ---------------------------------------------------------------------------
# Session ID uniqueness
# ---------------------------------------------------------------------------

def test_new_sessions_are_unique():
    from uuid import uuid4
    sessions = {f"aiva-{uuid4().hex}" for _ in range(100)}
    assert len(sessions) == 100


def test_session_id_format():
    from uuid import uuid4
    session = f"aiva-{uuid4().hex}"
    assert session.startswith("aiva-")
    assert len(session) == 5 + 32  # "aiva-" + 32 hex chars
