"""Test MQTT subscription."""
import paho.mqtt.client as mqtt
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def on_connect(client, userdata, flags, rc):
    """Callback when client connects to the broker."""
    print("Connected with result code "+str(rc))
    # Subscribe to all sensor topics
    client.subscribe("plant/sensors/#")

def on_message(client, userdata, msg):
    """Callback when a message is received."""
    try:
        data = json.loads(msg.payload.decode())
        print(f"Topic: {msg.topic}")
        print(f"Data: {json.dumps(data, indent=2)}")
        print("-" * 50)
    except Exception as e:
        print(f"Error processing message: {str(e)}")

def main():
    """Main function to test MQTT subscription."""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(os.getenv("MQTT_BROKER"), int(os.getenv("MQTT_PORT")))
        print("Waiting for messages... Press Ctrl+C to exit")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        client.disconnect()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
