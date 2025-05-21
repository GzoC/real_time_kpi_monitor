"""Test alert service API."""
from fastapi.testclient import TestClient
import pytest
from src.alerts.api import app
from src.db.models import Alert

client = TestClient(app)

def test_create_alert(test_db):
    """Test creating a new alert."""
    response = client.post(
        "/alerts/",
        json={
            "kpi_id": 1,
            "severity": "warning",
            "message": "Test alert"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "warning"
    assert data["message"] == "Test alert"
    
def test_get_alerts(test_db):
    """Test getting all alerts."""
    # Create test alert
    alert = Alert(kpi_id=1, severity="warning", message="Test alert")
    test_db.add(alert)
    test_db.commit()
    
    response = client.get("/alerts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["message"] == "Test alert"
    
def test_acknowledge_alert(test_db):
    """Test acknowledging an alert."""
    # Create test alert
    alert = Alert(kpi_id=1, severity="warning", message="Test alert")
    test_db.add(alert)
    test_db.commit()
    
    response = client.put(f"/alerts/{alert.id}/acknowledge")
    assert response.status_code == 200
    
    updated_alert = test_db.query(Alert).filter(Alert.id == alert.id).first()
    assert updated_alert.acknowledged == 1
