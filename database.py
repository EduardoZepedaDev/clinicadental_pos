import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path  # 👈 NUEVO

DB_ENGINE = "sqlite"
DB_PATH = "clinica.db"
ABS_DB_PATH = str(Path(DB_PATH).resolve())  # 👈 NUEVO

SERVICIOS_SEED = [
    "Prótesis flexible bilateral (2 a 4 dientes)",
    "Provisional de acrílico",
    "Prueba de glucosa externo",
    "Pulpectomía / Pulpotomía",
    "Radiografía",
    "Rebase",
    "Resina (cavidades amplias, sin garantía, solo Terakal)",
    "Resinas simples",
    "Selladores de fosetas",
    "Incrustación de resina",
    "Incrustación de zirconia",
    "Incrustación de metal",
    "Incrustación de silicato de litio",
    "Desensibilizante por unidad",
    "Corona de zirconio estratificada (estética)",
    "Anclaje",
    "Amalgama",
    "Blanqueamiento",
    "Cementación por muñón",
    "Cirugía de 3er molar",
    "Corona IMAX estratificada",
    "Corona de zirconia (cada diente normal)",
    "Corona IMAX monolítica",
    "Corona metal porcelana",
    "Corona libre de metal",
    "Carillas de resina",
    "Curación (4 sesiones)",
    "Curetaje / colgajo por arcada",
    "Desgaste (prótesis externas)",
    "Endodoncia de centrales y laterales",
    "Endodoncia de caninos y premolares",
    "Endodoncia de molares",
    "Endopostes",
    "Extracción de restos radiculares",
    "Extracción simple",
    "Guarda flexible, rígida",
    "Corona de acrílico (sin garantía)",
    "Jacket (polividrio / resina SIGNUM)",
    "Limpieza (profilaxis)",
    "Mantenedor de espacio",
    "Prótesis acrílico bilateral, total",
    "Prótesis acrílico unilateral",
    "Prótesis flexible total (Valplast)",
    "Prótesis flexible unilateral (1 a 2 dientes)",
    "Retirar brackets sup./inf. + limpieza (externos)",
    "Retiro de brackets + limpieza (externos)",
    "Consulta pacientes externos",
    "Trampa de dedo fija",
    "Trampa de dedo removible",
    "Tratamiento de ortodoncia invisible",
    "Tratamiento de ortodoncia BD. mini",
    "Retenedores pacientes de la clínica",
    "Retenedores pacientes externos",
    "Gingivectomía",
    "Gingivectomía completa arriba y abajo",
    "Retiro de trampa",
    "Un implante",
    "Dos implantes o más",
    "Apicectomía",
    "Cirugía mucocele",
    "Plaquita expansora",
    "Frenilectomía",
    "Retenedor fijo",
    "Retenedor PETG (clínica)",
    "Retenedor por segmentos",
    "Trainer",
    "Cirugía de anclaje",
    "Gingivectomía por cuadrante",
]

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
    print(f"[DB] Usando base de datos en: {ABS_DB_PATH}")  # 👈 debug útil
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

    # Servicios (creamos tabla si no existe; el UNIQUE lo aseguramos con un índice)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    """)
    # Aseguramos unicidad por nombre SIN romper esquemas previos
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_servicios_nombre ON servicios(nombre)")

    # Ventas
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

    # Migración defensiva por si la tabla existía sin 'servicios_texto'
    cols = {r[1] for r in cur.execute("PRAGMA table_info('ventas')").fetchall()}
    if "servicios_texto" not in cols:
        cur.execute("ALTER TABLE ventas ADD COLUMN servicios_texto TEXT NOT NULL DEFAULT ''")
        # Nota: 'servicio_id' casi seguro no existe ya; dejamos el backfill como opcional
        if "servicio_id" in cols:
            cur.execute("""
                UPDATE ventas
                SET servicios_texto = (
                    SELECT s.nombre FROM servicios s WHERE s.id = ventas.servicio_id
                )
                WHERE servicios_texto = '' AND servicio_id IS NOT NULL
            """)

    # 👉 Seed: rellena faltantes (inserta todo si está vacía; ignora duplicados si ya hay)
    total_antes, total_despues, insertados = seed_servicios_fill_missing(con)
    print(f"[SEED] Servicios antes: {total_antes}, después: {total_despues}, insertados: {insertados}")

    con.commit()
    con.close()

def seed_servicios_fill_missing(con):
    """
    Inserta todos los servicios del seed usando INSERT OR IGNORE.
    - Si la tabla está vacía: inserta todos.
    - Si ya hay algunos: inserta solo los faltantes.
    Devuelve (total_antes, total_despues, insertados).
    """
    cur = con.cursor()

    # Garantiza tabla e índice único
    cur.execute("""
        CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    """)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_servicios_nombre ON servicios(nombre)")

    cur.execute("SELECT COUNT(*) FROM servicios")
    total_antes = cur.fetchone()[0]

    cur.executemany("INSERT OR IGNORE INTO servicios (nombre) VALUES (?)",
                    [(s,) for s in SERVICIOS_SEED])

    cur.execute("SELECT COUNT(*) FROM servicios")
    total_despues = cur.fetchone()[0]
    insertados = total_despues - total_antes

    con.commit()
    return total_antes, total_despues, insertados



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
