"""
timescale_connector.py
Define el engine de SQLAlchemy y crea la tabla 'sensor_data' en TimescaleDB.
"""

import pg8000
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
from src.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

def test_connection():
    """Prueba la conexión directamente con pg8000."""
    try:
        print(f"Intentando conexión con: host={DB_HOST}, port={DB_PORT}, dbname={DB_NAME}, user={DB_USER}")
        conn = pg8000.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version()')
        version = cursor.fetchone()
        print("✅ Conexión exitosa a PostgreSQL:", version[0])
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print("❌ Error al conectar:", str(e))
        return False

def init_db():
    """
    Crea las tablas definidas en metadata.
    Si la tabla ya existe, no hace nada.
    """
    if not test_connection():
        raise Exception("No se pudo establecer conexión con la base de datos")
        
    try:
        # Crear el engine de SQLAlchemy usando pg8000
        engine = create_engine(
            f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
            echo=True
        )
        
        # Metadata recogerá la definición de tablas
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
        
        # Crear las tablas
        metadata.create_all(engine)
        print("✅ Tabla 'sensor_data' creada o ya existente.")
        
    except SQLAlchemyError as e:
        print("❌ Error al crear tablas:", e)
        raise
