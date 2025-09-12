import sqlite3
import pandas as pd
from datetime import datetime

DB_ENGINE = "sqlite"

def get_connection():
    if DB_ENGINE == "sqlite":
        return sqlite3.connect("clinica.db")

def init_db():
    con = get_connection()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS servicios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        precio REAL NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        servicio_id INTEGER,
        fecha TEXT,
        monto REAL,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id),
        FOREIGN KEY (servicio_id) REFERENCES servicios(id)
    )""")
    con.commit()
    con.close()

# ---------------- CLIENTES (CRD) ----------------
def agregar_cliente(nombre, telefono):
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO clientes(nombre, telefono) VALUES (?, ?)", (nombre, telefono))
    con.commit()
    con.close()

def obtener_clientes():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT * FROM clientes")
    rows = cur.fetchall()
    con.close()
    return rows

def eliminar_cliente(cliente_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
    con.commit()
    con.close()

# ---------------- SERVICIOS (CRD) ----------------
def agregar_servicio(nombre, precio):
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO servicios(nombre, precio) VALUES (?, ?)", (nombre, precio))
    con.commit()
    con.close()

def obtener_servicios():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT * FROM servicios")
    rows = cur.fetchall()
    con.close()
    return rows

def eliminar_servicio(servicio_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM servicios WHERE id=?", (servicio_id,))
    con.commit()
    con.close()

# ---------------- VENTAS (CRD) ----------------
def registrar_venta(cliente_id, servicio_id, monto):
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO ventas(cliente_id, servicio_id, fecha, monto) VALUES (?, ?, ?, ?)",
                (cliente_id, servicio_id, datetime.now().strftime("%Y-%m-%d %H:%M"), monto))
    con.commit()
    con.close()

def obtener_ventas():
    query = """
    SELECT v.id, c.nombre as cliente, s.nombre as servicio, v.monto, v.fecha
    FROM ventas v
    LEFT JOIN clientes c ON v.cliente_id = c.id
    LEFT JOIN servicios s ON v.servicio_id = s.id
    ORDER BY v.fecha DESC
    """
    con = get_connection()
    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    con.close()
    return rows

def eliminar_venta(venta_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM ventas WHERE id=?", (venta_id,))
    con.commit()
    con.close()

# ---------------- REPORTES (DataFrames) ----------------
def df_clientes():
    con = get_connection()
    df = pd.read_sql("SELECT * FROM clientes", con)
    con.close()
    return df

def df_servicios():
    con = get_connection()
    df = pd.read_sql("SELECT * FROM servicios", con)
    con.close()
    return df

def df_ventas():
    query = """
    SELECT v.id, c.nombre as cliente, s.nombre as servicio, v.monto, v.fecha
    FROM ventas v
    LEFT JOIN clientes c ON v.cliente_id = c.id
    LEFT JOIN servicios s ON v.servicio_id = s.id
    """
    con = get_connection()
    df = pd.read_sql(query, con)
    con.close()
    return df
