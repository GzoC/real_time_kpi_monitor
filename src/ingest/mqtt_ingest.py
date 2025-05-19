#!/usr/bin/env python3
"""
mqtt_ingest.py
Simula datos de sensores leyendo un CSV y publicándolos vía MQTT.
Cada línea del CSV se envía como un mensaje JSON al tópico especificado.
"""

import csv                                             # Leer archivos CSV
import json                                            # Construir payload JSON
import time                                            # Controlar intervalos de publicación
import argparse                                        # Parsear argumentos de línea de comandos
import paho.mqtt.client as mqtt                        # Cliente MQTT

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

    # Crear cliente MQTT
    client = mqtt.Client()
    # Conecta al broker usando host y puerto
    client.connect(args.broker, args.port)
    # Arranca el loop en background para manejar reconexiones
    client.loop_start()

    # Abre el CSV para leer las mediciones
    with open(args.csv, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Construye un diccionario con los datos
            data = {
                "sensor_id": row["sensor_id"],
                "timestamp": row["timestamp"],
                # Convierte el valor a float para garantizar tipo numérico
                "value": float(row["value"])
            }
            # Serializa el diccionario a JSON
            payload = json.dumps(data)
            # Publica el mensaje en el tópico indicado
            client.publish(args.topic, payload)
            # Muestra en consola lo que se ha publicado
            print(f"[MQTT] Publicado en {args.topic}: {payload}")
            # Espera el intervalo definido antes de la siguiente emisión
            time.sleep(args.interval)

    # Detiene el loop y cierra la conexión
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
