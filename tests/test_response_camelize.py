from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_camelize_response_keys():
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "msg" in data
    assert "data" in data
    assert "totalSymbols" in data["data"]
    assert "activeStrategies" in data["data"]
    assert "lastBacktest" in data["data"]
    assert "health" in data["data"]
