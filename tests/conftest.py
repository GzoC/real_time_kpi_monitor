"""
conftest.py
Configuración común para las pruebas con pytest.
"""

import pytest
import os
import logging
from pathlib import Path

@pytest.fixture(autouse=True)
def setup_test_logging():
    """Configura logging para las pruebas."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

@pytest.fixture
def test_data_dir():
    """Directorio para datos de prueba."""
    return Path(__file__).parent / 'test_data'

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Configura variables de entorno para pruebas."""
    test_env = {
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

def pytest_configure(config):
    """Configura marcadores de pytest."""
    config.addinivalue_line("markers", "db: marca pruebas relacionadas con la base de datos")
    config.addinivalue_line("markers", "mqtt: marca pruebas relacionadas con MQTT")
    config.addinivalue_line("markers", "integration: marca pruebas de integración")

@pytest.fixture(scope='session')
def docker_compose_file(pytestconfig):
    """Archivo docker-compose para pruebas."""
    return os.path.join(str(pytestconfig.rootdir), 'docker', 'docker-compose.test.yml')
