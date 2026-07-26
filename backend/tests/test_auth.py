from __future__ import annotations

from datetime import timedelta

from app.core.security import create_access_token


def registration_payload(**overrides):
    payload = {
        "full_name": "Lakshana K",
        "email": "lakshana@example.com",
        "password": "Strong@123",
        "preferred_language": "English",
    }
    payload.update(overrides)
    return payload


def test_successful_registration_and_default_preferences(client, db_session):
    response = client.post("/api/auth/register", json=registration_payload())
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["email"] == "lakshana@example.com"
    assert "password_hash" not in data

    from app.models.user import UserPreference

    preference = db_session.query(UserPreference).filter_by(user_id=data["id"]).one()
    assert preference.preferred_currency == "INR"
    assert preference.preferred_language == "English"


def test_duplicate_registration(client):
    assert client.post("/api/auth/register", json=registration_payload()).status_code == 201
    response = client.post("/api/auth/register", json=registration_payload())
    assert response.status_code == 409


def test_email_is_normalized(client):
    response = client.post(
        "/api/auth/register",
        json=registration_payload(email="Lakshana@Example.COM"),
    )
    assert response.status_code == 201
    assert response.json()["data"]["email"] == "lakshana@example.com"


def test_registration_validation(client):
    cases = [
        registration_payload(email="not-an-email"),
        registration_payload(password="short"),
        registration_payload(password="lowercase@123"),
        registration_payload(password="UPPERCASE@123"),
        registration_payload(password="NoNumber@"),
        registration_payload(password="NoSpecial123"),
        registration_payload(preferred_language="French"),
    ]
    for payload in cases:
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 422


def test_successful_login(client, user_factory):
    user_factory()
    response = client.post(
        "/api/auth/login",
        json={"email": "LAKSHANA@EXAMPLE.COM", "password": "Strong@123"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert data["expires_at"]
    assert "password_hash" not in data["user"]


def test_invalid_login_credentials(client, user_factory):
    user_factory()
    wrong = client.post(
        "/api/auth/login",
        json={"email": "lakshana@example.com", "password": "Wrong@123"},
    )
    unknown = client.post(
        "/api/auth/login",
        json={"email": "unknown@example.com", "password": "Wrong@123"},
    )
    assert wrong.status_code == 401
    assert unknown.status_code == 401
    assert wrong.json()["error"]["message"] == unknown.json()["error"]["message"]


def test_inactive_user_cannot_login(client, user_factory):
    user_factory(active=False)
    response = client.post(
        "/api/auth/login",
        json={"email": "lakshana@example.com", "password": "Strong@123"},
    )
    assert response.status_code == 401


def test_current_user_requires_valid_token(client, user_factory):
    user = user_factory()
    missing = client.get("/api/auth/me")
    invalid = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
    missing_user_token = create_access_token("99999", {"email": "missing@example.com"})
    missing_user = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {missing_user_token}"}
    )
    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert missing_user.status_code == 401


def test_current_user_success(client, auth_header):
    response = client.get("/api/auth/me", headers=auth_header)
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "lakshana@example.com"
    assert "password_hash" not in response.json()["data"]
