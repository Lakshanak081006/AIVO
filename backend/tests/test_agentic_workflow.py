from __future__ import annotations

from app.agents.requirement_agent import extract_requirements, missing_fields
from app.agents.scoring import rank_hotels, rank_transport
from app.simulated_apis.services import travel_data_service


def test_requirement_extraction_complete():
    data = extract_requirements(
        "Plan a two-day trip from Coimbatore to Chennai for two people next weekend under ₹20000. I prefer train travel and museums."
    )
    assert data["source"] == "Coimbatore"
    assert data["destination"] == "Chennai"
    assert data["traveller_count"] == 2
    assert data["budget"] == 20000
    assert data["transport_preference"] == "TRAIN"
    assert not missing_fields(data)


def test_transport_and_hotel_ranking():
    transports = [
        {"total_price": 1000, "duration_minutes": 400, "rating": 4.2, "transport_type": "TRAIN", "available": True, "cancellation_policy": "Free cancellation"},
        {"total_price": 800, "duration_minutes": 500, "rating": 4.0, "transport_type": "BUS", "available": True, "cancellation_policy": "Partial"},
    ]
    hotels = [
        {"total_price": 3000, "rating": 4.5, "distance_from_city_centre": 2, "amenities": ["Wi-Fi", "Breakfast"], "available": True, "cancellation_policy": "Free cancellation"},
        {"total_price": 2000, "rating": 3.8, "distance_from_city_centre": 5, "amenities": ["Wi-Fi"], "available": True, "cancellation_policy": "Partial"},
    ]
    assert rank_transport(transports, "TRAIN")[0]["normalized_score"] > 0
    assert rank_hotels(hotels)[0]["normalized_score"] > 0


def test_full_agentic_plan(client, auth_header):
    response = client.post(
        "/api/travel/plan",
        headers=auth_header,
        json={
            "instruction": "Plan a two-day trip from Coimbatore to Chennai for two people next weekend under ₹20000. I prefer train travel and museums.",
            "response_language": "English",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    data = body["data"]
    assert data["status"] == "READY"
    assert data["selected_transport"]
    assert data["selected_hotel"]
    assert len(data["itinerary"]) == 2
    assert data["budget_breakdown"]["total_cost"] > 0
    assert data["progress"]["percentage"] >= 90


def test_clarification_flow(client, auth_header):
    response = client.post(
        "/api/travel/plan",
        headers=auth_header,
        json={"instruction": "Plan a trip from Coimbatore to Chennai.", "response_language": "English"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "clarification_required"
    assert "budget" in data["missing_fields"]


def test_budget_alternative_and_feedback(client, auth_header):
    response = client.post(
        "/api/travel/plan",
        headers=auth_header,
        json={
            "instruction": "Plan a three-day trip from Coimbatore to Mumbai for two people next weekend under ₹5000.",
            "response_language": "English",
        },
    )
    assert response.status_code == 200
    plan_id = response.json()["plan_id"]
    alt = client.get(f"/api/travel/plans/{plan_id}/alternatives", headers=auth_header)
    assert alt.status_code == 200
    assert alt.json()["data"]["original_total"] > 0
    feedback = client.post(
        f"/api/travel/plans/{plan_id}/feedback",
        headers=auth_header,
        json={"overall_rating": 4, "preference_tags": ["Prefer trains"], "text_feedback": "Good plan"},
    )
    assert feedback.status_code == 200
    prefs = client.get("/api/users/preferences", headers=auth_header).json()["data"]
    assert any(item["field"] == "preferred_transport_type" for item in prefs["pending_suggestions"])


def test_simulated_failure_uses_fallback(client, auth_header):
    travel_data_service.set_failure("hotel", "error")
    response = client.post(
        "/api/travel/plan",
        headers=auth_header,
        json={
            "instruction": "Plan a two-day trip from Coimbatore to Bengaluru for two people next weekend under ₹25000.",
            "response_language": "English",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    travel_data_service.set_failure("hotel", None)
