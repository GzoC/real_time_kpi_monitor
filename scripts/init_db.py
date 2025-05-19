# scripts/init_db.py
import sys
import os

# Agrega la ruta del proyecto al sistema para que Python encuentre src/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.db.timescale_connector import init_db
from src.config import SQLALCHEMY_DATABASE_URL

if __name__ == "__main__":
    print("Cadena de conexión:", SQLALCHEMY_DATABASE_URL)
    init_db()
