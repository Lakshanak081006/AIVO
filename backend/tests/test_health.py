def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "running"
    assert payload["name"] == "Autonomous Personal Assistant"


def test_application_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_database_health(client):
    response = client.get("/api/health/database")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}
