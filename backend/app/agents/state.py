from __future__ import annotations
from typing import Any, TypedDict
class TravelAgentState(TypedDict, total=False):
    user_id: int
    request_id: int
    plan_id: int
    original_instruction: str
    detected_language: str
    response_language: str
    extracted_requirements: dict[str, Any]
    missing_fields: list[str]
    tasks: list[dict[str, Any]]
    current_agent: str
    current_task: str
    completed_tasks: list[str]
    failed_tasks: list[str]
    retry_counts: dict[str,int]
    transport_options: list[dict[str, Any]]
    hotel_options: list[dict[str, Any]]
    attractions: list[dict[str, Any]]
    weather_data: list[dict[str, Any]]
    selected_transport: dict[str, Any]
    selected_hotel: dict[str, Any]
    selected_attractions: list[dict[str, Any]]
    itinerary: list[dict[str, Any]]
    budget_breakdown: dict[str, Any]
    alternatives: dict[str, Any]
    progress_percentage: int
    workflow_status: str
    final_summary: str
    errors: list[dict[str, Any]]
