"""
Script de prueba para verificar la conexión a la base de datos.
"""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

import pg8000
from src.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

def test_db_connection():
    print(f"Intentando conectar a la base de datos...")
    print(f"Host: {DB_HOST}")
    print(f"Puerto: {DB_PORT}")
    print(f"Base de datos: {DB_NAME}")
    print(f"Usuario: {DB_USER}")
    
    try:
        conn = pg8000.Connection(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print("Conexión exitosa! Resultado de prueba:", result)
        
        cursor.close()
        conn.close()
        print("Conexión cerrada correctamente.")
        return True
        
    except Exception as e:
        print(f"Error al conectar: {str(e)}")
        print(f"Tipo de error: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_db_connection()
