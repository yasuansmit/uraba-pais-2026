import sqlite3
import mysql.connector


conn_sqlite = sqlite3.connect('uraba_pais.db')
conn_sqlite.row_factory = sqlite3.Row
cursor_sqlite = conn_sqlite.cursor()


conn_mysql = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",  
    database="uraba_pais_db"
)
cursor_mysql = conn_mysql.cursor()

# 3. Obtener las tablas
cursor_sqlite.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tablas = [r[0] for r in cursor_sqlite.fetchall()]

# 4. Migrar datos
for tabla in tablas:
    cursor_sqlite.execute(f"SELECT * FROM {tabla}")
    filas = cursor_sqlite.fetchall()
    if not filas:
        continue
    
    columnas = filas[0].keys()
    cols_str = ", ".join(columnas)
    placeholders = ", ".join(["%s"] * len(columnas))
    query = f"INSERT INTO {tabla} ({cols_str}) VALUES ({placeholders})"
    
    datos = [tuple(f) for f in filas]
    cursor_mysql.executemany(query, datos)
    conn_mysql.commit()
    print(f"✓ Tabla '{tabla}' migrada con éxito ({len(filas)} filas).")

conn_sqlite.close()
conn_mysql.close()
print("\n¡Migración finalizada con éxito!")