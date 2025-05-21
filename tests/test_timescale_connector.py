"""
test_timescale_connector.py
Pruebas unitarias para el módulo timescale_connector.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError
from src.db.timescale_connector import (
    create_engine_with_pool,
    test_connection,
    init_db
)

@pytest.fixture
def mock_engine():
    """Fixture que proporciona un engine mock."""
    engine = MagicMock()
    engine.connect.return_value = MagicMock()
    return engine

@pytest.mark.db
def test_create_engine_with_pool():
    """Prueba la creación del pool de conexiones."""
    with patch('src.db.timescale_connector.create_engine') as mock_create_engine:
        create_engine_with_pool()
        mock_create_engine.assert_called_once()
        args, kwargs = mock_create_engine.call_args
        assert 'pool_size' in kwargs
        assert 'max_overflow' in kwargs
        assert 'pool_timeout' in kwargs

@pytest.mark.db
def test_test_connection_success(mock_engine):
    """Prueba conexión exitosa a la base de datos."""
    with patch('src.db.timescale_connector.create_engine_with_pool', return_value=mock_engine):
        mock_engine.connect().execute().scalar.return_value = 'PostgreSQL 12.3'
        assert test_connection() is True

@pytest.mark.db
def test_test_connection_failure(mock_engine):
    """Prueba conexión fallida a la base de datos."""
    with patch('src.db.timescale_connector.create_engine_with_pool', return_value=mock_engine):
        mock_engine.connect.side_effect = SQLAlchemyError("Connection failed")
        assert test_connection() is False

@pytest.mark.db
def test_init_db_success(mock_engine):
    """Prueba inicialización exitosa de la base de datos."""
    with patch('src.db.timescale_connector.create_engine_with_pool', return_value=mock_engine), \
         patch('src.db.timescale_connector.test_connection', return_value=True):
        init_db()
        mock_engine.connect.assert_called()

@pytest.mark.db
def test_init_db_connection_failure():
    """Prueba fallo de conexión durante la inicialización."""
    with patch('src.db.timescale_connector.test_connection', return_value=False), \
         pytest.raises(Exception) as exc_info:
        init_db()
        assert "No se pudo establecer conexión" in str(exc_info.value)

@pytest.mark.db
def test_init_db_creation_failure(mock_engine):
    """Prueba fallo en la creación de tablas."""
    with patch('src.db.timescale_connector.create_engine_with_pool', return_value=mock_engine), \
         patch('src.db.timescale_connector.test_connection', return_value=True):
        mock_engine.connect.side_effect = SQLAlchemyError("Table creation failed")
        with pytest.raises(SQLAlchemyError):
            init_db()
