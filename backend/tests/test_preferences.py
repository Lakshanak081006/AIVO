from __future__ import annotations


def test_get_default_preferences(client, auth_header):
    response = client.get("/api/users/preferences", headers=auth_header)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["preferred_currency"] == "INR"
    assert data["tourist_interests"] == []


def test_update_preferences_and_normalize_values(client, auth_header):
    response = client.put(
        "/api/users/preferences",
        headers=auth_header,
        json={
            "preferred_currency": "usd",
            "preferred_transport_type": "TRAIN",
            "minimum_hotel_rating": 3.5,
            "maximum_hotel_distance": 12,
            "tourist_interests": ["Museums", " museums ", "Historical places"],
            "avoid_early_morning": True,
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["preferred_currency"] == "USD"
    assert data["preferred_transport_type"] == "TRAIN"
    assert data["tourist_interests"] == ["Museums", "Historical places"]


def test_invalid_preference_values(client, auth_header):
    cases = [
        {"preferred_currency": "RUPEES"},
        {"minimum_hotel_rating": 6},
        {"maximum_hotel_distance": -1},
        {"preferred_transport_type": "SHIP"},
        {},
    ]
    for payload in cases:
        response = client.put("/api/users/preferences", headers=auth_header, json=payload)
        assert response.status_code == 422


def test_preferences_require_authentication(client):
    assert client.get("/api/users/preferences").status_code == 401


def add_suggestion(db_session, user_factory, suggestion):
    user = user_factory()
    preference = user.preference
    preference.pending_suggestions = [suggestion]
    db_session.commit()
    db_session.refresh(preference)
    return preference


def test_approve_preference_suggestion(client, db_session, user_factory):
    suggestion = {
        "id": "suggestion-1",
        "field": "preferred_transport_type",
        "suggested_value": "TRAIN",
        "reason": "Selected train repeatedly",
        "source": "feedback",
        "status": "PENDING",
    }
    add_suggestion(db_session, user_factory, suggestion)
    login = client.post(
        "/api/auth/login",
        json={"email": "lakshana@example.com", "password": "Strong@123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    response = client.post(
        "/api/users/preferences/confirm",
        headers=headers,
        json={"suggestion_id": "suggestion-1", "decision": "APPROVED"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["preferred_transport_type"] == "TRAIN"
    assert data["pending_suggestions"][0]["status"] == "APPROVED"


def test_reject_preference_suggestion(client, db_session, user_factory):
    suggestion = {
        "id": "suggestion-2",
        "field": "avoid_early_morning",
        "suggested_value": True,
        "reason": "Feedback preference",
        "source": "feedback",
        "status": "PENDING",
    }
    add_suggestion(db_session, user_factory, suggestion)
    login = client.post(
        "/api/auth/login",
        json={"email": "lakshana@example.com", "password": "Strong@123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    response = client.post(
        "/api/users/preferences/confirm",
        headers=headers,
        json={"suggestion_id": "suggestion-2", "decision": "REJECTED"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["avoid_early_morning"] is False
    assert data["pending_suggestions"][0]["status"] == "REJECTED"


def test_missing_or_processed_suggestion(client, db_session, user_factory):
    suggestion = {
        "id": "suggestion-3",
        "field": "preferred_transport_type",
        "suggested_value": "BUS",
        "status": "APPROVED",
    }
    add_suggestion(db_session, user_factory, suggestion)
    login = client.post(
        "/api/auth/login",
        json={"email": "lakshana@example.com", "password": "Strong@123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    missing = client.post(
        "/api/users/preferences/confirm",
        headers=headers,
        json={"suggestion_id": "missing", "decision": "APPROVED"},
    )
    processed = client.post(
        "/api/users/preferences/confirm",
        headers=headers,
        json={"suggestion_id": "suggestion-3", "decision": "APPROVED"},
    )
    assert missing.status_code == 404
    assert processed.status_code == 409
