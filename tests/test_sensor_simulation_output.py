# tests/test_sensor_simulation_output.py (was test_ingestor.py)
import unittest
import os
import json
import time
import subprocess # For running script

OUTPUT_FILE = "./test_sensor_data_simulation.jsonl"

class TestSensorSimulationFileOutput(unittest.TestCase):

    def setUp(self):
        os.environ["SIMULATION_OUTPUT"] = "file"
        os.environ["SIMULATION_OUTPUT_FILE"] = OUTPUT_FILE
        os.environ["SIMULATION_INTERVAL_SECONDS"] = "0.1" # Faster simulation for test
        os.environ["SIMULATION_MAX_ITERATIONS"] = "2" # Generate a few records (2 iterations * 3 readings/iteration = 6 lines)
        
        # Ensure output file is clean before the test
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)

    def tearDown(self):
        # Clean up output file after the test
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
        
        # Unset environment variables to avoid affecting other tests
        del os.environ["SIMULATION_OUTPUT"]
        del os.environ["SIMULATION_OUTPUT_FILE"]
        del os.environ["SIMULATION_INTERVAL_SECONDS"]
        del os.environ["SIMULATION_MAX_ITERATIONS"]

    def test_simulate_sensors_writes_to_file(self):
        # Run simulate_sensors.py as a subprocess.
        # This assumes simulate_sensors.py has been modified to respect SIMULATION_MAX_ITERATIONS.
        # The script should exit automatically after the specified number of iterations.
        # A timeout is added as a safeguard.
        try:
            process = subprocess.run(
                ["python", "scripts/simulate_sensors.py"], 
                capture_output=True, 
                text=True, 
                timeout=10, # Increased timeout slightly to ensure script completion
                check=True # Will raise CalledProcessError if return code is non-zero
            )
            # Optional: print stdout/stderr for debugging if needed
            print("Simulate sensors stdout:", process.stdout)
            print("Simulate sensors stderr:", process.stderr)

        except subprocess.CalledProcessError as e:
            self.fail(f"simulate_sensors.py failed with return code {e.returncode}\nstdout:\n{e.stdout}\nstderr:\n{e.stderr}")
        except subprocess.TimeoutExpired:
            self.fail("simulate_sensors.py timed out. Check SIMULATION_MAX_ITERATIONS.")

        self.assertTrue(os.path.exists(OUTPUT_FILE), f"Sensor data output file '{OUTPUT_FILE}' was not created.")
        
        line_count = 0
        expected_lines = int(os.environ["SIMULATION_MAX_ITERATIONS"]) * 3 # 3 sensor readings per iteration
        
        with open(OUTPUT_FILE, "r") as f:
            for line_number, line in enumerate(f, 1):
                line_count += 1
                try:
                    data = json.loads(line.strip())
                    self.assertIn("sensor_id", data, f"Line {line_number} missing 'sensor_id'")
                    self.assertIn("value", data, f"Line {line_number} missing 'value'")
                    self.assertIn("timestamp", data, f"Line {line_number} missing 'timestamp'")
                    # Check for specific sensor_ids if needed
                    self.assertIn(data["sensor_id"], ["STATUS001", "SPEED001", "QUALITY001"])
                except json.JSONDecodeError:
                    self.fail(f"Invalid JSON in output file at line {line_number}: {line.strip()}")
        
        self.assertEqual(line_count, expected_lines, f"Incorrect number of lines in output file. Expected {expected_lines}, got {line_count}.")

if __name__ == '__main__':
    unittest.main()
