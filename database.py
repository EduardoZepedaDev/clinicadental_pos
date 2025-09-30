import sqlite3
import pandas as pd
from datetime import datetime

DB_ENGINE = "sqlite"
DB_PATH = "clinica.db"


# =========================
# Conexión / Inicialización
# =========================
def get_connection():
    if DB_ENGINE == "sqlite":
        con = sqlite3.connect(DB_PATH)
        con.execute("PRAGMA foreign_keys = ON;")
        return con
    raise ValueError(f"DB_ENGINE no soportado: {DB_ENGINE}")


def init_db():
    con = get_connection()
    cur = con.cursor()

    # Clientes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL
        )
    """)

    # Servicios (solo nombre)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    """)

    # Ventas (ahora monto lo pone el usuario)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            servicios_texto TEXT NOT NULL,  -- nombres concatenados
            fecha TEXT NOT NULL,
            monto REAL NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)
    cols = {r[1] for r in cur.execute("PRAGMA table_info('ventas')").fetchall()}
    if "servicios_texto" not in cols:
        cur.execute("ALTER TABLE ventas ADD COLUMN servicios_texto TEXT NOT NULL DEFAULT ''")
        # backfill usando servicio_id si existe
        if "servicio_id" in cols:
            cur.execute("""
                UPDATE ventas
                SET servicios_texto = (
                    SELECT s.nombre FROM servicios s WHERE s.id = ventas.servicio_id
                )
                WHERE servicios_texto = '' AND servicio_id IS NOT NULL
            """)
    con.commit()
    con.close()


# =========================
# CLIENTES (CRD)
# =========================
def agregar_cliente(nombre, telefono):
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO clientes(nombre, telefono) VALUES (?, ?)", (nombre, telefono))
    con.commit()
    con.close()


def obtener_clientes():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT id, nombre, telefono FROM clientes ORDER BY id DESC")
    rows = cur.fetchall()
    con.close()
    return rows


def eliminar_cliente(cliente_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
    con.commit()
    con.close()


# =========================
# SERVICIOS (CRD)
# =========================
def agregar_servicio(nombre):
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO servicios(nombre) VALUES (?)", (nombre,))
    con.commit()
    con.close()


def obtener_servicios():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT id, nombre FROM servicios ORDER BY id DESC")
    rows = cur.fetchall()
    con.close()
    return rows


def eliminar_servicio(servicio_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM servicios WHERE id=?", (servicio_id,))
    con.commit()
    con.close()


# =========================
# VENTAS
# =========================
def registrar_venta(cliente_id: int, servicios_seleccionados: list, monto: float) -> int:
    """
    Crea una venta.
    - cliente_id: int
    - servicios_seleccionados: lista de nombres de servicios
    - monto: lo escribe el usuario
    """
    if not servicios_seleccionados:
        raise ValueError("Debes seleccionar al menos un servicio.")

    servicios_texto = ", ".join(servicios_seleccionados)
    fecha_txt = datetime.now().strftime("%Y-%m-%d %H:%M")

    con = get_connection()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO ventas (cliente_id, servicios_texto, fecha, monto)
        VALUES (?, ?, ?, ?)
    """, (cliente_id, servicios_texto, fecha_txt, float(monto)))
    venta_id = cur.lastrowid
    con.commit()
    con.close()

    return venta_id


def obtener_ventas():
    query = """
    SELECT v.id, c.nombre AS cliente, v.servicios_texto, v.monto, v.fecha
    FROM ventas v
    JOIN clientes c ON c.id = v.cliente_id
    ORDER BY v.fecha DESC, v.id DESC
    """
    con = get_connection()
    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    con.close()
    return rows


def eliminar_venta(venta_id: int):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM ventas WHERE id=?", (venta_id,))
    con.commit()
    con.close()


def obtener_venta_por_id(venta_id: int):
    con = get_connection()
    cur = con.cursor()
    cur.execute("""
        SELECT v.id, v.cliente_id, v.servicios_texto, v.monto, v.fecha
        FROM ventas v
        WHERE v.id = ?
    """, (venta_id,))
    venta = cur.fetchone()
    con.close()
    return venta


# =========================
# REPORTES (DataFrames)
# =========================
def df_clientes():
    con = get_connection()
    df = pd.read_sql("SELECT id, nombre, telefono FROM clientes ORDER BY id DESC", con)
    con.close()
    return df


def df_servicios():
    con = get_connection()
    df = pd.read_sql("SELECT id, nombre FROM servicios ORDER BY id DESC", con)
    con.close()
    return df


def df_ventas():
    query = """
    SELECT v.id, c.nombre AS cliente, v.servicios_texto, v.monto, v.fecha
    FROM ventas v
    JOIN clientes c ON c.id = v.cliente_id
    ORDER BY v.fecha DESC, v.id DESC
    """
    con = get_connection()
    df = pd.read_sql(query, con)
    con.close()
    return df   
