"""MQTT client for ingesting sensor data."""
import paho.mqtt.client as mqtt
from loguru import logger
import json
import os
from dotenv import load_dotenv
from datetime import datetime

from ..db.database import SessionLocal
from ..db.models import SensorReading

# Load environment variables
load_dotenv()

class MQTTClient:
    def __init__(self):
        self.broker = os.getenv("MQTT_BROKER", "localhost")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.topic = os.getenv("MQTT_TOPIC", "plant/sensors/#")
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback when client connects to the broker."""
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
            client.subscribe(self.topic)
        else:            logger.error(f"Failed to connect to MQTT Broker with code {rc}")
            
    def on_message(self, client, userdata, msg):
        """Callback when a message is received from the broker."""
        try:
            payload = json.loads(msg.payload.decode())
            reading = SensorReading(
                time=datetime.utcnow(),
                sensor_id=payload.get("sensor_id"),
                value=payload.get("value"),
                unit=payload.get("unit")
            )
            
            # Save to database
            db = SessionLocal()
            db.add(reading)
            db.commit()
            db.close()
            
            logger.debug(f"Saved sensor reading: {reading.sensor_id} = {reading.value} {reading.unit}")
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            
    def start(self):
        """Start the MQTT client and connect to broker."""
        try:
            logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port)
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Stopping MQTT client...")
            self.client.disconnect()
        except Exception as e:
            logger.error(f"Error in MQTT client: {str(e)}")
            raise

if __name__ == "__main__":
    client = MQTTClient()
    client.start()
