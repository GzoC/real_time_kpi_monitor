# scripts/simulate_sensors.py
import json
import random
import time
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

# Conditional import for Kafka related modules
SIMULATION_OUTPUT = os.getenv("SIMULATION_OUTPUT", "kafka").lower()
KAFKA_DEFAULT_TOPIC = 'sensor_data' # Default topic name if using Kafka

if SIMULATION_OUTPUT == "kafka":
    try:
        from src.ingestor import get_kafka_producer, publish_message
    except ImportError:
        logging.error("Failed to import Kafka modules from src.ingestor. Ensure it's available if SIMULATION_OUTPUT is kafka.")
        # Depending on strictness, might exit or set Kafka mode to unavailable
        # For now, this will cause an error later if Kafka mode is selected and imports failed.

# Load environment variables
load_dotenv()

# Configure logging
# Using basicConfig here for simplicity if this script is run standalone.
# If part of a larger app, logging might be configured centrally.
logging.basicConfig(level=os.getenv("LOG_LEVEL_SIMULATOR", "INFO"), 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_FILE_PATH = os.getenv("SIMULATION_OUTPUT_FILE", "./sensor_data_simulation.jsonl")

def simulate_sensors():
    logger.info(f"Sensor simulation started. Output mode: {SIMULATION_OUTPUT}")
    
    producer = None
    output_file = None

    if SIMULATION_OUTPUT == "kafka":
        try:
            producer = get_kafka_producer() # This function should handle its own logging for success/failure
            if not producer:
                logger.error("Failed to get Kafka producer. Exiting simulation as Kafka output is selected.")
                return
        except NameError: # Handles case where Kafka modules couldn't be imported
            logger.error("Kafka modules not available. Cannot run in Kafka output mode. Exiting.")
            return
            
    elif SIMULATION_OUTPUT == "file":
        try:
            # Ensure directory exists if OUTPUT_FILE_PATH includes directories
            os.makedirs(os.path.dirname(OUTPUT_FILE_PATH) or '.', exist_ok=True)
            output_file = open(OUTPUT_FILE_PATH, "a")
            logger.info(f"Outputting sensor data to file: {OUTPUT_FILE_PATH}")
        except IOError as e:
            logger.error(f"Failed to open output file {OUTPUT_FILE_PATH}: {e}. Exiting simulation.")
            return
    else:
        logger.error(f"Invalid SIMULATION_OUTPUT mode: {SIMULATION_OUTPUT}. Must be 'kafka' or 'file'. Exiting.")
        return

    machine_running = True
    downtime_probability = 0.01 # Per data point, not per minute for faster testing if sleep is short
    
    # Get max iterations from environment variable
    max_iterations_str = os.getenv("SIMULATION_MAX_ITERATIONS")
    max_iterations = 0
    if max_iterations_str and max_iterations_str.isdigit() and int(max_iterations_str) > 0:
        max_iterations = int(max_iterations_str)
        logger.info(f"Simulation will run for {max_iterations} iterations.")
    
    iterations = 0
    try:
        while True: # Loop will be broken by max_iterations or KeyboardInterrupt
            if max_iterations > 0 and iterations >= max_iterations:
                logger.info(f"Reached maximum simulation iterations ({max_iterations}). Stopping.")
                break
            iterations += 1
            
            current_time_iso = datetime.now().isoformat()
            
            if random.random() < downtime_probability:
                machine_running = not machine_running
            
            status_key = "STATUS001"
            status_data = {
                "sensor_id": status_key,
                "value": 1 if machine_running else 0,
                "unit": "binary",
                "timestamp": current_time_iso
            }
            
            speed_key = "SPEED001"
            base_speed = 80.0
            speed = base_speed * random.uniform(0.9, 1.1) if machine_running else 0.0
            speed_data = {
                "sensor_id": speed_key,
                "value": round(speed, 2),
                "unit": "units/hour",
                "timestamp": current_time_iso
            }
            
            quality_key = "QUALITY001"
            quality = random.uniform(0.93, 1.0) if machine_running else 0.0
            quality_data = {
                "sensor_id": quality_key,
                "value": round(quality, 3),
                "unit": "ratio",
                "timestamp": current_time_iso
            }
            
            data_to_log = [status_data, speed_data, quality_data]

            if SIMULATION_OUTPUT == "kafka" and producer:
                try:
                    publish_message(producer, KAFKA_DEFAULT_TOPIC, status_key, status_data)
                    publish_message(producer, KAFKA_DEFAULT_TOPIC, speed_key, speed_data)
                    publish_message(producer, KAFKA_DEFAULT_TOPIC, quality_key, quality_data)
                    logger.info(f"Published sensor data to Kafka topic '{KAFKA_DEFAULT_TOPIC}' for timestamp {current_time_iso}")
                except NameError: # publish_message not defined due to import error
                    logger.error("Kafka publish_message function not available. Cannot send data to Kafka.")
                    # Potentially stop simulation or switch mode if critical
                    break 
                except Exception as e:
                    logger.error(f"Error publishing to Kafka: {e}")
                    # Handle specific Kafka errors if needed
                    break # Or continue, depending on desired robustness

            elif SIMULATION_OUTPUT == "file" and output_file:
                try:
                    for data_item in data_to_log:
                        output_file.write(json.dumps(data_item) + "\n")
                    output_file.flush() # Ensure data is written to disk periodically
                    logger.info(f"Written sensor data to file '{OUTPUT_FILE_PATH}' for timestamp {current_time_iso}")
                except IOError as e:
                    logger.error(f"IOError writing to file {OUTPUT_FILE_PATH}: {e}. Stopping simulation.")
                    break # Stop simulation if file writing fails
                except Exception as e:
                    logger.error(f"Unexpected error writing to file: {e}")
                    break

            # Simulation interval - configurable via env var or fixed
            simulation_interval_seconds = float(os.getenv("SIMULATION_INTERVAL_SECONDS", "5.0")) # Default to 5.0s
            time.sleep(simulation_interval_seconds)
            
    except KeyboardInterrupt:
        logger.info("Sensor simulation stopped by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during simulation: {e}", exc_info=True)
    finally:
        if SIMULATION_OUTPUT == "kafka" and producer:
            try:
                producer.flush()
                producer.close()
                logger.info("Kafka producer closed.")
            except NameError: # producer might not be defined if get_kafka_producer failed
                pass
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
        
        if SIMULATION_OUTPUT == "file" and output_file:
            try:
                output_file.close()
                logger.info(f"Output file {OUTPUT_FILE_PATH} closed.")
            except IOError as e:
                logger.error(f"Error closing output file {OUTPUT_FILE_PATH}: {e}")

if __name__ == "__main__":
    # Example: To run with file output for testing:
    # export SIMULATION_OUTPUT="file"
    # export SIMULATION_OUTPUT_FILE="./sensor_data_test.jsonl"
    # export LOG_LEVEL_SIMULATOR="DEBUG"
    # python scripts/simulate_sensors.py
    simulate_sensors()
