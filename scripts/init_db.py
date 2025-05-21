# scripts/init_db.py
import sys
import os
from pathlib import Path

# Obtener la ruta absoluta al directorio raíz del proyecto
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

print("Python path:", sys.path)
print("Directorio actual:", os.getcwd())
print("Raíz del proyecto:", project_root)

try:
    from src.db.timescale_connector import init_db, test_connection
    from src.config import DB_HOST, DB_PORT, DB_USER, DB_NAME
    
    print("\nConfiguración de base de datos:")
    print(f"Host: {DB_HOST}")
    print(f"Puerto: {DB_PORT}")
    print(f"Usuario: {DB_USER}")
    print(f"Base de datos: {DB_NAME}")
    
    print("\nProbando conexión...")
    if test_connection():
        print("\nInicializando base de datos...")
        init_db()
except Exception as e:
    print("❌ Error:", str(e))
    print("Tipo de error:", type(e).__name__)
