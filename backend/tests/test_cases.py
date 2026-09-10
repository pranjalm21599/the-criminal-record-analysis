from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["active", "degraded"]

def test_create_case():
    payload = {
        "case_number": "TEST-001",
        "title": "Test Case",
        "description": "Integration test case"
    }
    response = client.post("/cases/", json=payload)
    assert response.status_code == 200
    assert response.json()["case_number"] == "TEST-001"