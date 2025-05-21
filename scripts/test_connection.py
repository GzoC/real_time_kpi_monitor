"""
test_connection.py
Script simple para probar la conexión a TimescaleDB usando pg8000 directamente.
"""
import sys
import os
from pathlib import Path

# Agregar la raíz del proyecto al path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
import pg8000.native

def test_direct_connection():
    """Prueba la conexión directamente con pg8000."""
    print("\nIntentando conexión con los siguientes parámetros:")
    print(f"Host: {DB_HOST}")
    print(f"Puerto: {DB_PORT}")
    print(f"Usuario: {DB_USER}")
    print(f"Base de datos: {DB_NAME}")
    
    try:
        # Intenta establecer una conexión directa
        conn = pg8000.native.Connection(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        # Ejecuta una consulta simple
        version = conn.run("SELECT version();")
        print("\n✅ Conexión exitosa!")
        print(f"Versión de PostgreSQL: {version[0][0]}")
        
        # Cierra la conexión
        conn.close()
        return True
        
    except Exception as e:
        print("\n❌ Error de conexión:")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        return False

if __name__ == "__main__":
    test_direct_connection()
