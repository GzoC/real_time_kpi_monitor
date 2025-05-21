#!/usr/bin/env python3
"""
mqtt_ingest.py
Simula datos de sensores leyendo un CSV y publicándolos vía MQTT.
Cada línea del CSV se envía como un mensaje JSON al tópico especificado.
"""

import csv
import json
import time
import argparse
import logging
from datetime import datetime
from typing import Dict, Any
import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage
import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 5  # segundos

class MQTTPublisher:
    def __init__(self, broker: str, port: int, topic: str):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = mqtt.Client()
        self.connected = False
        self.setup_callbacks()

    def setup_callbacks(self):
        """Configura los callbacks del cliente MQTT."""
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

    def on_connect(self, client, userdata, flags, rc):
        """Callback cuando se establece la conexión."""
        if rc == 0:
            self.connected = True
            logger.info("✅ Conectado al broker MQTT")
        else:
            logger.error(f"❌ Error de conexión al broker MQTT (código {rc})")

    def on_disconnect(self, client, userdata, rc):
        """Callback cuando se pierde la conexión."""
        self.connected = False
        if rc != 0:
            logger.warning("Desconexión inesperada del broker MQTT")

    def on_publish(self, client, userdata, mid):
        """Callback cuando se publica un mensaje."""
        logger.debug(f"Mensaje {mid} publicado correctamente")

    def connect(self) -> bool:
        """Intenta conectar al broker MQTT con reintentos."""
        attempt = 0
        while attempt < MAX_RECONNECT_ATTEMPTS:
            try:
                self.client.connect(self.broker, self.port)
                self.client.loop_start()
                return True
            except Exception as e:
                attempt += 1
                logger.error(f"Intento {attempt} fallido: {str(e)}")
                if attempt < MAX_RECONNECT_ATTEMPTS:
                    logger.info(f"Reintentando en {RECONNECT_DELAY} segundos...")
                    time.sleep(RECONNECT_DELAY)
        return False

    def disconnect(self):
        """Desconecta del broker MQTT."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Desconectado del broker MQTT")

    def publish(self, payload: Dict[str, Any]) -> bool:
        """Publica un mensaje en el tópico configurado."""
        if not self.connected:
            logger.error("No hay conexión al broker MQTT")
            return False

        try:
            msg_json = json.dumps(payload)
            info = self.client.publish(self.topic, msg_json, qos=1)
            if info.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Error al publicar mensaje: {info.rc}")
                return False
            logger.info(f"[MQTT] Publicado en {self.topic}: {msg_json}")
            return True
        except Exception as e:
            logger.error(f"Error al publicar mensaje: {str(e)}")
            return False

def validate_csv_data(df: pd.DataFrame) -> bool:
    """Valida el formato y contenido del CSV."""
    required_columns = ['sensor_id', 'timestamp', 'value']
    
    # Verificar columnas requeridas
    if not all(col in df.columns for col in required_columns):
        logger.error("Faltan columnas requeridas en el CSV")
        return False
    
    # Verificar tipos de datos
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['value'] = pd.to_numeric(df['value'])
    except Exception as e:
        logger.error(f"Error en formato de datos: {str(e)}")
        return False
    
    # Verificar valores nulos
    if df[required_columns].isna().any().any():
        logger.error("El CSV contiene valores nulos")
        return False
    
    return True

def parse_args():
    """Define y obtiene los parámetros de entrada del script."""
    parser = argparse.ArgumentParser(
        description="Simula sensores vía MQTT desde un archivo CSV"
    )
    parser.add_argument(
        "--csv",
        required=True,
        help="Ruta al archivo CSV con datos simulados"
    )
    parser.add_argument(
        "--broker",
        default="localhost",
        help="Host del broker MQTT (por defecto localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=1883,
        help="Puerto del broker MQTT (por defecto 1883)"
    )
    parser.add_argument(
        "--topic",
        default="sensors/data",
        help="Tópico MQTT donde se publican los datos"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Segundos de espera entre cada mensaje"
    )
    return parser.parse_args()

def main():
    # Leer argumentos
    args = parse_args()
    
    try:
        # Leer y validar CSV
        logger.info(f"Leyendo archivo CSV: {args.csv}")
        df = pd.read_csv(args.csv)
        if not validate_csv_data(df):
            raise ValueError("Datos del CSV inválidos")
        
        # Crear y conectar cliente MQTT
        publisher = MQTTPublisher(args.broker, args.port, args.topic)
        if not publisher.connect():
            raise ConnectionError("No se pudo conectar al broker MQTT")
        
        # Procesar y publicar datos
        for _, row in df.iterrows():
            data = {
                "sensor_id": row["sensor_id"],
                "timestamp": row["timestamp"],
                "value": float(row["value"])
            }
            
            if not publisher.publish(data):
                logger.warning(f"Fallo al publicar dato: {data}")
                continue
                
            time.sleep(args.interval)
        
        # Desconectar cliente
        publisher.disconnect()
        
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Ejecución interrumpida por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        exit(1)
