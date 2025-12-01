# tests/test_server_api.py
import pytest
from fastapi.testclient import TestClient
from server.src.main_server import app
from server.src.db.migrations import reset_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    reset_db()
    yield

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_products():
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    assert data[0]["article"] == "BOLT-M10"

def test_create_reception():
    payload = {
        "ttn_number": "API-TEST-001",
        "ttn_date": "2025-02-20",
        "supplier": "API Supplier",
        "items": [
            {
                "article": "BOLT-M10",
                "name": "Болт М10",
                "quantity": 50,
                "unit": "шт",
                "control_required": True,
                "suspicious_fields": []
            }
        ]
    }
    response = client.post("/api/v1/receptions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["ttn_number"] == "API-TEST-001"
    assert len(data["items"]) == 1

def test_get_receptions():
    # Create one first
    test_create_reception()
    
    response = client.get("/api/v1/receptions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["ttn_number"] == "API-TEST-001"

def test_update_control_results():
    # 1. Create reception
    payload = {
        "ttn_number": "CTRL-TEST",
        "ttn_date": "2025-02-20",
        "supplier": "Control Supplier",
        "items": [
            {
                "article": "BOLT-M10",
                "name": "Болт М10",
                "quantity": 10,
                "unit": "шт",
                "control_required": True
            }
        ]
    }
    create_resp = client.post("/api/v1/receptions", json=payload)
    reception_id = create_resp.json()["id"]
    item_id = create_resp.json()["items"][0]["id"]
    
    # 2. Update results
    update_payload = {
        "items": [
            {
                "id": item_id,
                "control_status": "passed",
                "control_result": {"passed": True, "message": "OK"},
                "notes": "All good"
            }
        ]
    }
    
    response = client.post(f"/api/v1/receptions/{reception_id}/control-results", json=update_payload)
    assert response.status_code == 200
    
    # 3. Check status
    data = response.json()
    assert data["status"] == "completed"
    assert data["items"][0]["control_status"] == "passed"
