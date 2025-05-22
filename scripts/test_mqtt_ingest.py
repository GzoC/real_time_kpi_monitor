"""Script temporal para probar la ingestión de datos MQTT."""
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "kpi_monitor")

# Crear URL y engine de base de datos
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

def on_connect(client, userdata, flags, rc):
    """Callback cuando el cliente se conecta al broker."""
    if rc == 0:
        print("¡Conectado al broker MQTT!")
        client.subscribe("plant/sensors/#")
    else:
        print(f"Error de conexión con código {rc}")

def on_message(client, userdata, msg):
    """Callback cuando se recibe un mensaje."""
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Recibido: {payload}")
        
        # Insertar en la base de datos
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO sensor_readings (time, sensor_id, value, unit)
                VALUES (NOW(), :sensor_id, :value, :unit)
            """), {
                "sensor_id": payload.get("sensor_id"),
                "value": payload.get("value"),
                "unit": payload.get("unit")
            })
            conn.commit()
            
        print(f"Guardado en BD: {payload}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    """Función principal."""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect("localhost", 1883)
        print("Iniciando cliente MQTT...")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo cliente...")
        client.disconnect()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
