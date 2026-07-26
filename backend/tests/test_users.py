from __future__ import annotations


def test_get_profile(client, auth_header):
    response = client.get("/api/users/profile", headers=auth_header)
    assert response.status_code == 200
    assert response.json()["data"]["full_name"] == "Lakshana K"


def test_update_profile_partially(client, auth_header):
    response = client.put(
        "/api/users/profile",
        headers=auth_header,
        json={"preferred_language": "Tamil"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["preferred_language"] == "Tamil"


def test_empty_or_invalid_profile_update_is_rejected(client, auth_header):
    empty = client.put("/api/users/profile", headers=auth_header, json={})
    invalid = client.put(
        "/api/users/profile",
        headers=auth_header,
        json={"preferred_language": "French"},
    )
    assert empty.status_code == 422
    assert invalid.status_code == 422


def test_profile_endpoints_require_authentication(client):
    assert client.get("/api/users/profile").status_code == 401
    assert client.put("/api/users/profile", json={"full_name": "New Name"}).status_code == 401
