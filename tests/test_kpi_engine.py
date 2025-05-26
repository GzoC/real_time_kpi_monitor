# tests/test_kpi_engine.py
import unittest
import os
import subprocess
import sqlite3
from datetime import datetime, timedelta, timezone # Ensure UTC is available if not Python 3.11+
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Assuming models and KPIEngine are importable
from src.db.models import Base, SensorReading, KPIValue, Alert # Import all relevant models
from src.processing.kpi_engine import KPIEngine
from src.db.database import SessionLocal as GlobalSessionLocal, engine as global_engine # To reconfigure

# Define test database file
TEST_DB_FILE = "./test_kpi_engine_data.db"
DATABASE_URL = f"sqlite:///{os.path.abspath(TEST_DB_FILE)}"

class TestKPIEngineSQLite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["DB_TYPE"] = "sqlite"
        os.environ["DATABASE_URL"] = DATABASE_URL 
        # SQLITE_DB_PATH is used by init_db.py if DATABASE_URL is not set for sqlite
        # os.environ["SQLITE_DB_PATH"] = os.path.abspath(TEST_DB_FILE) 

        # Ensure a clean state before any tests run
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)

        # Initialize the database schema using init_db.py
        try:
            # Ensure init_db uses the new DATABASE_URL for SQLite
            subprocess.run(["python", "scripts/init_db.py"], check=True, capture_output=True, text=True, timeout=15)
        except subprocess.CalledProcessError as e:
            print(f"init_db.py stderr: {e.stderr}")
            print(f"init_db.py stdout: {e.stdout}")
            raise AssertionError(f"init_db.py failed: {e.stderr}") from e
        
        # Reconfigure the global engine and SessionLocal in src.db.database
        # to use the test-specific SQLite database for this test class.
        # This is crucial if KPIEngine or other parts of the app import SessionLocal directly.
        global_engine.dispose() # Dispose of the old engine
        new_engine = create_engine(DATABASE_URL)
        GlobalSessionLocal.configure(bind=new_engine)
        # Update the global engine reference as well if other parts of the app use it directly
        # This is a bit of a hack; ideally, the app would use dependency injection for sessions.
        # For now, this ensures KPIEngine uses the test DB.
        import src.db.database
        src.db.database.engine = new_engine


    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
        # It might be good to reset os.environ variables if they were specific to this test class,
        # though unittest typically isolates classes.
        # For example, if DATABASE_URL was set only for this class:
        # del os.environ["DATABASE_URL"]
        # del os.environ["DB_TYPE"]

    def setUp(self):
        # Each test method will get a fresh session and can populate data as needed
        # The schema is already created by setUpClass.
        # We need to ensure tables are clean for each test method.
        engine = create_engine(DATABASE_URL) # Use the test DB URL
        Base.metadata.drop_all(engine) # Drop all tables
        Base.metadata.create_all(engine) # Recreate them

        self.Session = sessionmaker(bind=engine)
        self.session = self.Session()
        
        # The KPIEngine will use the globally reconfigured SessionLocal
        self.kpi_engine = KPIEngine() 
        # We override the kpi_engine's session to ensure it's specific to this test method's session
        # if KPIEngine allows setting its session, or if it always uses the global SessionLocal.
        # If KPIEngine creates its own session from the global SessionLocal, the global reconfig is key.
        # For safety, let's ensure KPIEngine uses this method's session if possible.
        # KPIEngine in the provided code does `self.db = SessionLocal()`. So global reconfig is vital.
        # To ensure test isolation for DB state, we can also pass a session to KPIEngine.
        # Modifying KPIEngine to accept a session would be cleaner: `KPIEngine(session=self.session)`
        # For now, assuming the global reconfigure + clean tables per test is sufficient.
        # Let's explicitly set the session for KPIEngine if it's using the global one.
        self.kpi_engine.db = self.session


    def tearDown(self):
        self.session.close()
        # Tables are dropped and recreated in setUp, so individual data cleanup per test is handled.

    def _insert_test_sensor_readings(self, readings_data):
        for data in readings_data:
            # Ensure timestamp is datetime object
            if isinstance(data['time'], str):
                data['time'] = datetime.fromisoformat(data['time'].replace('Z', '+00:00'))
            reading = SensorReading(**data)
            self.session.add(reading)
        self.session.commit()

    def test_oee_calculation_all_good(self):
        end_time = datetime.now(timezone.utc) # Changed UTC to timezone.utc
        start_time = end_time - timedelta(hours=1)
        
        test_readings = []
        # Availability: 100% (all 60 readings are status=1)
        for i in range(60):
            test_readings.append({"time": start_time + timedelta(minutes=i), "sensor_id": "STATUS001", "value": 1, "unit": "status"})
        # Performance: Target 80 units/hr, Ideal 90 units/hr. Perf = 80/90 = 0.888...
        # The KPI engine has a cap at 0.9 for performance, so 0.888 will be used.
        for i in range(60):
            test_readings.append({"time": start_time + timedelta(minutes=i), "sensor_id": "SPEED001", "value": 80, "unit": "units/hour"})
        # Quality: 95%
        for i in range(60):
            test_readings.append({"time": start_time + timedelta(minutes=i), "sensor_id": "QUALITY001", "value": 0.95, "unit": "ratio"})
        
        self._insert_test_sensor_readings(test_readings)

        oee = self.kpi_engine.calculate_oee(start_time, end_time)
        
        # Expected: Availability=1.0, Performance=80/90 (capped at 0.9 by engine logic, but actual is 0.888..), Quality=0.95
        # OEE = 1.0 * (80/90) * 0.95 = 1.0 * 0.8888... * 0.95 = 0.8444...
        self.assertAlmostEqual(oee, 1.0 * (80.0/90.0) * 0.95, places=3)

        # Verify saved KPI values
        oee_kpi = self.session.query(KPIValue).filter_by(kpi_name="OEE").first()
        self.assertIsNotNone(oee_kpi)
        self.assertAlmostEqual(oee_kpi.value, oee, places=3)
        self.assertEqual(oee_kpi.status, "warning") # 0.844 is below 0.85 warning for OEE

    def test_availability_calculation_some_downtime(self):
        end_time = datetime.now(timezone.utc) # Changed UTC to timezone.utc
        start_time = end_time - timedelta(minutes=10) # Shorter period for clarity
        
        test_readings = []
        # 8 out of 10 readings are status=1 (80% availability)
        for i in range(10):
            status_val = 1 if i < 8 else 0
            test_readings.append({"time": start_time + timedelta(minutes=i), "sensor_id": "STATUS001", "value": status_val, "unit": "status"})
        
        self._insert_test_sensor_readings(test_readings)
        
        availability = self.kpi_engine._calculate_availability(start_time, end_time)
        self.assertAlmostEqual(availability, 0.8, places=3)

        # Test saving and alert generation (indirectly via OEE calc or directly if methods are public)
        self.kpi_engine._save_kpi_value("availability", availability, end_time)
        avail_kpi = self.session.query(KPIValue).filter_by(kpi_name="availability").first()
        self.assertIsNotNone(avail_kpi)
        self.assertEqual(avail_kpi.status, "warning") # 0.8 is warning (>= critical_threshold)

        # Check for alert
        self.kpi_engine._check_and_create_alert("availability", availability, end_time)
        alert = self.session.query(Alert).filter_by(kpi_name="availability").first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "warning") # Severity should match the status


    def test_no_data_scenario(self):
        end_time = datetime.now(timezone.utc) # Changed UTC to timezone.utc
        start_time = end_time - timedelta(hours=1)

        # No data inserted

        availability = self.kpi_engine._calculate_availability(start_time, end_time)
        self.assertEqual(availability, 1.0, "Availability should default to 1.0 if no status data")

        performance = self.kpi_engine._calculate_performance(start_time, end_time)
        self.assertEqual(performance, 1.0, "Performance should default to 1.0 if no speed data")
        
        quality = self.kpi_engine._calculate_quality(start_time, end_time)
        self.assertEqual(quality, 1.0, "Quality should default to 1.0 if no quality data")

        oee = self.kpi_engine.calculate_oee(start_time, end_time)
        self.assertEqual(oee, 1.0, "OEE should be 1.0 if all components default to 1.0")
        
        # Check that OEE was saved as normal
        oee_kpi = self.session.query(KPIValue).filter_by(kpi_name="OEE").first()
        self.assertIsNotNone(oee_kpi)
        self.assertEqual(oee_kpi.status, "normal")


if __name__ == '__main__':
    unittest.main()
