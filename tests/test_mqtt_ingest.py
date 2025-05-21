"""
test_mqtt_ingest.py
Pruebas unitarias para el módulo mqtt_ingest.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from src.ingest.mqtt_ingest import (
    MQTTPublisher,
    validate_csv_data
)

@pytest.fixture
def mock_mqtt_client():
    """Fixture que proporciona un cliente MQTT mock."""
    return MagicMock()

@pytest.fixture
def valid_df():
    """Fixture que proporciona un DataFrame válido."""
    return pd.DataFrame({
        'sensor_id': ['sensor1', 'sensor2'],
        'timestamp': ['2025-05-20 10:00:00', '2025-05-20 10:01:00'],
        'value': [23.5, 24.1]
    })

@pytest.mark.mqtt
def test_mqtt_publisher_init():
    """Prueba la inicialización del publicador MQTT."""
    with patch('paho.mqtt.client.Client') as mock_client:
        publisher = MQTTPublisher('localhost', 1883, 'test/topic')
        assert publisher.broker == 'localhost'
        assert publisher.port == 1883
        assert publisher.topic == 'test/topic'
        assert not publisher.connected

@pytest.mark.mqtt
def test_mqtt_publisher_connect_success(mock_mqtt_client):
    """Prueba conexión exitosa al broker MQTT."""
    with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
        publisher = MQTTPublisher('localhost', 1883, 'test/topic')
        mock_mqtt_client.connect.return_value = 0
        assert publisher.connect() is True

@pytest.mark.mqtt
def test_mqtt_publisher_connect_failure(mock_mqtt_client):
    """Prueba conexión fallida al broker MQTT."""
    with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
        publisher = MQTTPublisher('localhost', 1883, 'test/topic')
        mock_mqtt_client.connect.side_effect = Exception("Connection failed")
        assert publisher.connect() is False

@pytest.mark.mqtt
def test_mqtt_publisher_publish_success(mock_mqtt_client):
    """Prueba publicación exitosa de mensaje."""
    with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
        publisher = MQTTPublisher('localhost', 1883, 'test/topic')
        publisher.connected = True
        mock_mqtt_client.publish.return_value.rc = 0
        assert publisher.publish({'test': 'data'}) is True

@pytest.mark.mqtt
def test_mqtt_publisher_publish_failure(mock_mqtt_client):
    """Prueba fallo en la publicación de mensaje."""
    with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
        publisher = MQTTPublisher('localhost', 1883, 'test/topic')
        publisher.connected = True
        mock_mqtt_client.publish.return_value.rc = 1
        assert publisher.publish({'test': 'data'}) is False

@pytest.mark.mqtt
def test_validate_csv_data_valid(valid_df):
    """Prueba validación de datos CSV válidos."""
    assert validate_csv_data(valid_df) is True

@pytest.mark.mqtt
def test_validate_csv_data_missing_columns():
    """Prueba validación con columnas faltantes."""
    df = pd.DataFrame({
        'sensor_id': ['sensor1'],
        'value': [23.5]
    })
    assert validate_csv_data(df) is False

@pytest.mark.mqtt
def test_validate_csv_data_invalid_types():
    """Prueba validación con tipos de datos inválidos."""
    df = pd.DataFrame({
        'sensor_id': ['sensor1'],
        'timestamp': ['invalid_date'],
        'value': ['not_a_number']
    })
    assert validate_csv_data(df) is False

@pytest.mark.mqtt
def test_validate_csv_data_null_values():
    """Prueba validación con valores nulos."""
    df = pd.DataFrame({
        'sensor_id': ['sensor1'],
        'timestamp': ['2025-05-20 10:00:00'],
        'value': [None]
    })
    assert validate_csv_data(df) is False
