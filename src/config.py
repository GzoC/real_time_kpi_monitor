"""
config.py
Carga las variables de entorno definidas en el archivo .env y las expone como constantes
para que estén disponibles en todo el proyecto.
"""

import os   
from dotenv import load_dotenv

# Carga las variables desde el archivo .env
load_dotenv(encoding="utf-8")

# Parámetros individuales de conexión a la base de datos
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "changeme")
DB_NAME = os.getenv("DB_NAME", "kpi_monitor")

# Cadena de conexión completa para SQLAlchemy + pg8000
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
    
# Debug: imprime la cadena de conexión para verificar caracteres extraños
if __name__ == "__main__":
    print("Cadena de conexión generada:", SQLALCHEMY_DATABASE_URL)
