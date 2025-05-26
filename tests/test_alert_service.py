# tests/test_alert_service.py
import unittest
import os
import subprocess
from datetime import datetime, timezone # Ensure UTC is available
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Models and App
from src.db.models import Base, Alert, KPIValue # Import all relevant models
from src.alerts.alert_service import app, get_db # Import FastAPI app and get_db dependency
from src.db.database import SessionLocal as GlobalSessionLocal, engine as global_engine # To reconfigure

TEST_DB_FILE = "./test_alert_service_data.db"
DATABASE_URL = f"sqlite:///{os.path.abspath(TEST_DB_FILE)}"

# This engine and SessionLocal are specific to the test setup
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for the FastAPI app
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestAlertServiceSQLite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # No need to set os.environ["DB_TYPE"] or os.environ["DATABASE_URL"] globally for the app
        # because we are overriding the get_db dependency directly.
        # However, init_db.py script (if run) would need them.
        # For this test, we will manage schema directly.
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
        
        # Create all tables in the test database
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
        # Clear dependency overrides
        app.dependency_overrides.clear()


    def setUp(self):
        # Create a new session for each test
        self.session = TestingSessionLocal()
        self.client = TestClient(app)

        # Clean tables before each test
        for table in reversed(Base.metadata.sorted_tables):
            self.session.execute(table.delete())
        self.session.commit()


    def tearDown(self):
        self.session.close()


    def test_create_alert(self):
        """Test creating a new alert."""
        response = self.client.post(
            "/alerts/",
            json={
                "kpi_name": "OEE_Test",
                "severity": "warning",
                "message": "Test alert for OEE"
            }
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["severity"], "warning")
        self.assertEqual(data["message"], "Test alert for OEE")
        self.assertEqual(data["kpi_name"], "OEE_Test")
        self.assertIn("id", data)
        self.assertIn("time", data)

        # Verify in DB
        alert_in_db = self.session.query(Alert).filter(Alert.id == data["id"]).first()
        self.assertIsNotNone(alert_in_db)
        self.assertEqual(alert_in_db.kpi_name, "OEE_Test")

    def test_get_alerts(self):
        """Test getting all alerts."""
        # Create test alert directly in DB
        alert1 = Alert(
            kpi_name="OEE_Get_1",
            severity="warning",
            message="Test alert 1",
            time=datetime.now(timezone.utc) # Changed UTC to timezone.utc
        )
        alert2 = Alert(
            kpi_name="OEE_Get_2",
            severity="critical",
            message="Test alert 2",
            time=datetime.now(timezone.utc) # Changed UTC to timezone.utc
        )
        self.session.add_all([alert1, alert2])
        self.session.commit()
        
        response = self.client.get("/alerts/")
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["message"], "Test alert 1")
        self.assertEqual(data[1]["kpi_name"], "OEE_Get_2")

    def test_acknowledge_alert(self):
        """Test acknowledging an alert."""
        alert_time = datetime.now(timezone.utc) # Changed UTC to timezone.utc
        # Create test alert
        test_alert = Alert(
            kpi_name="AVAILABILITY_Ack",
            severity="critical",
            message="Test alert for acknowledgement",
            time=alert_time,
            acknowledged=0
        )
        self.session.add(test_alert)
        self.session.commit()
        self.session.refresh(test_alert) # Get the ID
        
        alert_id = test_alert.id
        
        response = self.client.put(f"/alerts/{alert_id}/acknowledge")
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["message"], "Alert acknowledged")
        self.assertEqual(data["alert_id"], alert_id)
        
        # Verify in DB
        self.session.expire_all() # Expire session to ensure fresh data is loaded
        updated_alert = self.session.query(Alert).filter(Alert.id == alert_id).first()
        self.assertIsNotNone(updated_alert)
        self.assertEqual(updated_alert.acknowledged, 1)

    def test_acknowledge_nonexistent_alert(self):
        """Test acknowledging a non-existent alert."""
        non_existent_alert_id = 99999
        response = self.client.put(f"/alerts/{non_existent_alert_id}/acknowledge")
        self.assertEqual(response.status_code, 404) # Based on current alert_service.py logic
        data = response.json()
        self.assertEqual(data["detail"], "Alert not found")


if __name__ == '__main__':
    unittest.main()
