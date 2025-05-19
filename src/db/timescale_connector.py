"""
timescale_connector.py
Define el engine de SQLAlchemy y crea la tabla 'sensor_data' en TimescaleDB.
"""

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    Float
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from src.config import SQLALCHEMY_DATABASE_URL

# 1. Crear el engine de SQLAlchemy usando la URL de conexión
engine: Engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# 2. Metadata recogerá la definición de tablas
metadata = MetaData()

# 3. Definir la tabla 'sensor_data'
sensor_data = Table(
    "sensor_data",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sensor_id", String(50), nullable=False),
    Column("timestamp", DateTime, nullable=False),
    Column("value", Float, nullable=False),
)

def init_db():
    """
    Crea las tablas definidas en metadata.
    Si la tabla ya existe, no hace nada.
    """
    try:
        # Crea la tabla en la base de datos
        metadata.create_all(engine)
        print("✅ Tabla 'sensor_data' creada o ya existente.")
    except SQLAlchemyError as e:
        print("❌ Error al crear tablas:", e)
        raise
