"""Simulate sensor data for testing."""
import paho.mqtt.client as mqtt
import json
import random
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def simulate_sensors():
    """Simulate sensor data and publish to MQTT broker."""
    client = mqtt.Client()
    
    try:
        client.connect(os.getenv("MQTT_BROKER"), int(os.getenv("MQTT_PORT")))
        
        while True:
            # Simulate temperature sensor
            temp_data = {
                "sensor_id": "TEMP001",
                "value": round(random.uniform(20, 30), 2),
                "unit": "°C"
            }
            
            # Simulate pressure sensor
            pressure_data = {
                "sensor_id": "PRES001",
                "value": round(random.uniform(1000, 1020), 2),
                "unit": "hPa"
            }
            
            # Publish data
            client.publish("plant/sensors/temperature", 
                         json.dumps(temp_data))
            client.publish("plant/sensors/pressure", 
                         json.dumps(pressure_data))
            
            # Wait 1 second before next reading
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping sensor simulation...")
        client.disconnect()
    except Exception as e:
        print(f"Error: {str(e)}")
        client.disconnect()

if __name__ == "__main__":
    simulate_sensors()
