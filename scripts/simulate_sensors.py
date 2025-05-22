"""Simulate sensor data for testing."""
import paho.mqtt.client as mqtt
import json
import random
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def simulate_sensors():
    """Simula datos de sensores y los publica al broker MQTT."""
    client = mqtt.Client()
    
    try:
        client.connect(os.getenv("MQTT_BROKER"), int(os.getenv("MQTT_PORT")))
        
        # Estado inicial de la máquina
        machine_running = True
        downtime_probability = 0.01  # 1% de probabilidad de fallo por minuto
        
        while True:
            current_time = datetime.now()
            
            # Simula el estado de la máquina (1 = ejecutando, 0 = detenida)
            if random.random() < downtime_probability:
                machine_running = not machine_running
            
            status_data = {
                "sensor_id": "STATUS001",
                "value": 1 if machine_running else 0,
                "unit": "binary"
            }
            
            # Simula la velocidad de producción
            base_speed = 80.0  # velocidad base (unidades/hora)
            if machine_running:
                speed = base_speed * random.uniform(0.9, 1.1)  # ±10% variación
            else:
                speed = 0.0
                
            speed_data = {
                "sensor_id": "SPEED001",
                "value": round(speed, 2),
                "unit": "units/hour"
            }
            
            # Simula la calidad del producto
            if machine_running:
                quality = random.uniform(0.93, 1.0)  # 93-100% calidad
            else:
                quality = 0.0
                
            quality_data = {
                "sensor_id": "QUALITY001",
                "value": round(quality, 3),
                "unit": "ratio"
            }
            
            # Publica todos los datos
            client.publish("plant/sensors/status", json.dumps(status_data))
            client.publish("plant/sensors/speed", json.dumps(speed_data))
            client.publish("plant/sensors/quality", json.dumps(quality_data))
            
            # Espera 1 minuto antes de la siguiente lectura
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\nStopping sensor simulation...")
        client.disconnect()
    except Exception as e:
        print(f"Error: {str(e)}")
        client.disconnect()

if __name__ == "__main__":
    simulate_sensors()
