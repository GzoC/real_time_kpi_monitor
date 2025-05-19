"""
config.py
Carga las variables de entorno definidas en el archivo .env y las expone como constantes
para que estén disponibles en todo el proyecto.
"""

import os   
from dotenv import load_dotenv

# Carga las variables desde el archivo .env ubicado en la raíz del proyecto
load_dotenv()

# Parámetros individuales de conexión a la base de datos (tomados del .env)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "changeme")
DB_NAME = os.getenv("DB_NAME", "kpi_monitor")

# Cadena de conexión completa para SQLAlchemy + psycopg2
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
