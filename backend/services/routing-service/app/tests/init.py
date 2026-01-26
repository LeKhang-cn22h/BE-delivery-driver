import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_optimize_route():
    payload = {
        "locations": [
            {"lat": 10.7769, "lng": 106.7009, "name": "TP.HCM"},
            {"lat": 10.8231, "lng": 106.6297, "name": "Tân Bình"},
            {"lat": 10.7546, "lng": 106.6789, "name": "Quận 1"},
            {"lat": 10.8142, "lng": 106.7240, "name": "Bình Thạnh"}
        ],  
        "start_index": 0
    }
    
    response = client.post("/api/v1/routes/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert len(data["route"]["order"]) == 4
    assert data["route"]["total_distance"] > 0

def test_health_check():
    response = client.get("/api/v1/routes/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"