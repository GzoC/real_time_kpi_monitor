import sys
import os

# Agrega la carpeta 'src/' al path de importación
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from config import SQLALCHEMY_DATABASE_URL

print("Cadena de conexión cargada:")
print(SQLALCHEMY_DATABASE_URL)
