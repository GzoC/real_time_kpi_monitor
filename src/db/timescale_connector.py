"""
timescale_connector.py
Define el engine de SQLAlchemy y crea la tabla 'sensor_data' en TimescaleDB.
"""

import logging
from contextlib import contextmanager
import pg8000
from sqlalchemy import (
    create_engine, 
    MetaData, 
    Table, 
    Column, 
    Integer, 
    String, 
    DateTime, 
    Float,
    Index,
    text
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
from src.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_engine_with_pool() -> Engine:
    """Crea un engine de SQLAlchemy con pool de conexiones."""
    return create_engine(
        f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        echo=True
    )

@contextmanager
def get_db_connection():
    """Context manager para manejar conexiones de base de datos."""
    engine = create_engine_with_pool()
    try:
        connection = engine.connect()
        yield connection
    finally:
        connection.close()
        engine.dispose()

def test_connection() -> bool:
    """Prueba la conexión directamente con pg8000."""
    try:
        logger.info(f"Intentando conexión con: host={DB_HOST}, port={DB_PORT}, dbname={DB_NAME}, user={DB_USER}")
        with get_db_connection() as conn:
            result = conn.execute(text('SELECT version()')).scalar()
            logger.info("✅ Conexión exitosa a PostgreSQL: %s", result)
            return True
    except Exception as e:
        logger.error("❌ Error al conectar: %s", str(e))
        return False

def init_db():
    """
    Crea las tablas definidas en metadata e inicializa hypertable.
    Si la tabla ya existe, no hace nada.
    """
    if not test_connection():
        raise Exception("No se pudo establecer conexión con la base de datos")
        
    try:
        engine = create_engine_with_pool()
        metadata = MetaData()
        
        # Definir la tabla 'sensor_data'
        sensor_data = Table(
            "sensor_data",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("sensor_id", String(50), nullable=False),
            Column("timestamp", DateTime, nullable=False),
            Column("value", Float, nullable=False),
        )
        
        # Crear índices para optimizar consultas
        Index('idx_sensor_timestamp', sensor_data.c.sensor_id, sensor_data.c.timestamp)
        Index('idx_timestamp', sensor_data.c.timestamp)
        
        # Crear las tablas
        metadata.create_all(engine)
        
        # Convertir a hypertable de TimescaleDB
        with engine.connect() as conn:
            try:
                conn.execute(text(
                    """
                    SELECT create_hypertable('sensor_data', 'timestamp', 
                        if_not_exists => TRUE,
                        chunk_time_interval => INTERVAL '1 day'
                    )
                    """
                ))
                logger.info("✅ Tabla 'sensor_data' configurada como hypertable")
            except Exception as e:
                logger.warning("Hypertable ya existe o error al crearla: %s", str(e))
        
        logger.info("✅ Inicialización de base de datos completada")
        
    except SQLAlchemyError as e:
        logger.error("❌ Error al crear tablas: %s", e)
        raise
