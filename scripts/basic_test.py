import os
os.environ['PGCLIENTENCODING'] = 'UTF8'

import psycopg2

try:
    conn_string = "host=localhost port=5432 dbname=kpi_monitor user=postgres password=changeme"
    print("Trying to connect:", conn_string)
    
    conn = psycopg2.connect(conn_string)
    print("Connected!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print("Query executed successfully!")
    
    cursor.close()
    conn.close()
    print("Connection closed.")
    
except Exception as e:
    print("Error:", str(e))
