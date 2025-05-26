# tests/test_etl.py
import unittest
import os
import json
import subprocess
import sqlite3
from datetime import datetime, timezone # For timestamp comparison

# Define test file paths globally for clarity
TEST_DB_FILE = "./test_kpi_monitor.db"
TEST_DATA_FILE = "./test_sensor_data_for_etl.jsonl"

class TestEtlProcessLocal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set environment variables that will be used by scripts
        os.environ["DB_TYPE"] = "sqlite"
        # IMPORTANT: Ensure the path used in DATABASE_URL is consistent with where the DB is created/checked
        os.environ["DATABASE_URL"] = f"sqlite:///{os.path.abspath(TEST_DB_FILE)}"
        os.environ["SQLITE_DB_PATH"] = os.path.abspath(TEST_DB_FILE) # For init_db.py if it uses this
        
        os.environ["ETL_INPUT_SOURCE"] = "file"
        os.environ["ETL_INPUT_FILE"] = os.path.abspath(TEST_DATA_FILE)
        
        # For generating test data using simulate_sensors.py
        os.environ["SIMULATION_OUTPUT"] = "file" # Ensure simulator writes to file
        os.environ["SIMULATION_OUTPUT_FILE"] = os.path.abspath(TEST_DATA_FILE) # Simulator writes to the ETL input file
        os.environ["SIMULATION_INTERVAL_SECONDS"] = "0.1" # Fast simulation
        os.environ["SIMULATION_MAX_ITERATIONS"] = "1" # One set of readings (3 lines typically)

    @classmethod
    def tearDownClass(cls):
        # Clean up environment variables after all tests in the class are done
        # This helps prevent interference if tests are run in sequence with others
        # in a larger test suite, though unittest typically isolates test classes.
        del os.environ["DB_TYPE"]
        del os.environ["DATABASE_URL"]
        if "SQLITE_DB_PATH" in os.environ: del os.environ["SQLITE_DB_PATH"]
        del os.environ["ETL_INPUT_SOURCE"]
        del os.environ["ETL_INPUT_FILE"]
        del os.environ["SIMULATION_OUTPUT"]
        del os.environ["SIMULATION_OUTPUT_FILE"]
        del os.environ["SIMULATION_INTERVAL_SECONDS"]
        del os.environ["SIMULATION_MAX_ITERATIONS"]


    def setUp(self):
        # Clean up files before each test method
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
        if os.path.exists(TEST_DATA_FILE):
            os.remove(TEST_DATA_FILE)
        
        # Run init_db.py to create tables in the test SQLite DB
        # Ensure that init_db.py correctly uses DATABASE_URL or SQLITE_DB_PATH for SQLite
        try:
            subprocess.run(["python", "scripts/init_db.py"], check=True, capture_output=True, text=True, timeout=10)
        except subprocess.CalledProcessError as e:
            self.fail(f"init_db.py failed: {e.stderr}\n{e.stdout}")


    def tearDown(self):
        # Clean up files after each test method
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
        if os.path.exists(TEST_DATA_FILE):
            os.remove(TEST_DATA_FILE)

    def test_etl_processes_file_to_sqlite_db(self):
        # 1. Generate test data directly or by using simulate_sensors.py
        # For this test, we'll create a small sample data file for better control and predictability.
        sample_data = [
            {"sensor_id": "TEMP001", "value": 25.5, "unit": "C", "timestamp": "2023-01-01T10:00:00Z"},
            {"sensor_id": "HUM001", "value": 60.1, "unit": "%", "timestamp": "2023-01-01T10:00:05Z"},
            {"sensor_id": "STATUS001", "value": 1, "unit": "binary", "timestamp": "2023-01-01T10:00:10Z"}
        ]
        with open(TEST_DATA_FILE, "w") as f:
            for record in sample_data:
                f.write(json.dumps(record) + "\n")
        
        self.assertTrue(os.path.exists(TEST_DATA_FILE), "Test data file was not created.")

        # 2. Run the ETL script (src.etl.main)
        try:
            etl_process = subprocess.run(["python", "src/etl.py"], check=True, capture_output=True, text=True, timeout=15)
            # print("ETL stdout:", etl_process.stdout) # For debugging
            # print("ETL stderr:", etl_process.stderr) # For debugging
        except subprocess.CalledProcessError as e:
            self.fail(f"etl.py failed with return code {e.returncode}\nstdout:\n{e.stdout}\nstderr:\n{e.stderr}")
        except subprocess.TimeoutExpired:
            self.fail("etl.py timed out.")


        # 3. Verify the data in the SQLite database
        self.assertTrue(os.path.exists(TEST_DB_FILE), "SQLite DB file was not created by ETL process.")
        
        conn = None
        try:
            conn = sqlite3.connect(TEST_DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT sensor_id, value, unit, time FROM sensor_readings ORDER BY time ASC")
            rows = cursor.fetchall()
        except sqlite3.Error as e:
            self.fail(f"SQLite error during data verification: {e}")
        finally:
            if conn:
                conn.close()

        self.assertEqual(len(rows), len(sample_data), "Incorrect number of rows inserted into DB.")
        
        for i, expected in enumerate(sample_data):
            self.assertEqual(rows[i][0], expected["sensor_id"]) # sensor_id
            self.assertAlmostEqual(float(rows[i][1]), float(expected["value"]), places=3) # value
            self.assertEqual(rows[i][2], expected["unit"]) # unit
            
            # Compare timestamps carefully
            # SQLAlchemy for SQLite stores datetime as strings 'YYYY-MM-DD HH:MM:SS.ffffff'
            # The input timestamp is 'YYYY-MM-DDTHH:MM:SSZ'
            # We need to parse both to datetime objects for reliable comparison
            db_timestamp_str = rows[i][3]
            # Ensure db_timestamp_str is not None
            self.assertIsNotNone(db_timestamp_str, f"Timestamp for row {i} is None.")

            # Parse DB timestamp (typically UTC if stored from timezone-aware datetime)
            # The format from SQLAlchemy for SQLite with timezone=True is typically ISO format.
            try:
                # datetime.fromisoformat can handle various ISO 8601 formats, including those with or without Z,
                # and with or without microseconds.
                db_dt = datetime.fromisoformat(db_timestamp_str)
                # Ensure it's offset-aware UTC for comparison if it's naive
                if db_dt.tzinfo is None:
                    db_dt = db_dt.replace(tzinfo=timezone.utc)
                else: # If it has tzinfo, convert to UTC
                    db_dt = db_dt.astimezone(timezone.utc)

            except ValueError as e:
                self.fail(f"Could not parse database timestamp '{db_timestamp_str}': {e}")

            # Parse expected timestamp
            expected_dt = datetime.fromisoformat(expected["timestamp"].replace('Z', '+00:00'))
            
            self.assertEqual(db_dt, expected_dt, f"Timestamp mismatch for row {i}. DB: {db_dt}, Expected: {expected_dt}")

if __name__ == '__main__':
    unittest.main()
