import os

# Forzar codificación ASCII
os.environ['LANG'] = 'C'
os.environ['LC_ALL'] = 'C'
os.environ['PGCLIENTENCODING'] = 'SQL_ASCII'

import pg8000

print("Probando conexion a PostgreSQL usando pg8000...")

try:
    conn = pg8000.connect(
        database='kpi_monitor',
        user='postgres',
        password='changeme',
        host='localhost',
        port=5432
    )
    
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    print("Consulta de prueba exitosa:", result)
    
    cursor.close()
    conn.close()
    print("Conexion cerrada correctamente.")
    
except Exception as e:
    print(f"Error al conectar: {str(e)}")
    print("Tipo de error:", type(e).__name__)
