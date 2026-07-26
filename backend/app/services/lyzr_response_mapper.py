from __future__ import annotations

import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

# Fields that must be present for planning to proceed
REQUIRED_FIELDS = ["source", "destination", "start_date", "end_date", "traveller_count", "budget"]


def _safe_str(value: Any, default: str | None = None) -> str | None:
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def _safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        s = value.strip()
        if s:
            try:
                return date.fromisoformat(s)
            except ValueError:
                pass
    return None


def _safe_list(value: Any) -> list:
    if isinstance(value, list):
        return [str(x) for x in value if x is not None]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def map_lyzr_to_requirements(lyzr_result: dict[str, Any]) -> dict[str, Any]:
    """Convert a normalized Lyzr response dict into the same shape that
    extract_requirements() returns so WorkflowService can use it directly.
    """
    reqs: dict[str, Any] = lyzr_result.get("requirements") or {}

    # Dates
    start = _safe_date(reqs.get("start_date"))
    end = _safe_date(reqs.get("end_date"))

    # Duration
    duration = _safe_int(reqs.get("trip_duration_days"))
    if start and end and not duration:
        duration = (end - start).days + 1

    # Travellers
    travellers = _safe_int(reqs.get("traveller_count")) or _safe_int(reqs.get("travellers"))

    # Budget
    budget = _safe_float(reqs.get("budget")) or _safe_float(reqs.get("total_budget"))

    # Transport preference — normalise to uppercase
    transport_pref = _safe_str(reqs.get("transport_preference"))
    if transport_pref:
        transport_pref = transport_pref.upper()

    # Hotel rating
    hotel_rating = _safe_float(reqs.get("minimum_hotel_rating"))

    # Interests
    interests = _safe_list(reqs.get("tourist_interests") or reqs.get("interests"))

    # Special requirements
    special = _safe_list(reqs.get("special_requirements") or reqs.get("special"))

    # Language
    language = _safe_str(lyzr_result.get("language")) or "English"

    mapped: dict[str, Any] = {
        "source": _safe_str(reqs.get("source")),
        "destination": _safe_str(reqs.get("destination")),
        "start_date": start,
        "end_date": end,
        "trip_duration_days": duration,
        "traveller_count": travellers,
        "budget": budget,
        "currency": _safe_str(reqs.get("currency")) or "INR",
        "transport_preference": transport_pref,
        "hotel_preference": _safe_str(reqs.get("hotel_preference")),
        "minimum_hotel_rating": hotel_rating,
        "food_preference": _safe_str(reqs.get("food_preference")),
        "tourist_interests": interests,
        "special_requirements": special,
        "detected_language": language,
        "response_language": language,
    }

    logger.debug("Lyzr mapped requirements: %s", {k: v for k, v in mapped.items() if v is not None})
    return mapped


def extract_clarification(lyzr_result: dict[str, Any]) -> tuple[list[str], str | None]:
    """Return (missing_fields, clarification_question) from a Lyzr result."""
    missing = _safe_list(lyzr_result.get("missing_fields"))
    question = _safe_str(lyzr_result.get("clarification_question"))
    return missing, question


def extract_decision_summary(lyzr_result: dict[str, Any]) -> dict[str, Any]:
    """Pull decision_summary, warnings, confidence from a Lyzr result safely."""
    return {
        "decision_summary": _safe_str(lyzr_result.get("decision_summary")),
        "warnings": _safe_list(lyzr_result.get("warnings")),
        "confidence": _safe_float(lyzr_result.get("confidence")),
    }
