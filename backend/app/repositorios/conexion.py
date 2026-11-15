import sqlite3
from pathlib import Path

from .. import config

SCHEMA = Path(__file__).with_name("schema.sql")


def get_conn(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or config.DB_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")   # evita "database is locked" ante accesos concurrentes
    conn.execute("PRAGMA synchronous = NORMAL")  # con WAL: seguro ante corte de energía, sin perder rendimiento
    return conn


def init_db(db_path: str | None = None) -> None:
    conn = get_conn(db_path)
    try:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        _migrar(conn)
        conn.commit()
    finally:
        conn.close()


def _migrar(conn: sqlite3.Connection) -> None:
    """Bases creadas antes de agregar columnas: las añade sin perder datos."""
    col_perfil = {f["name"] for f in conn.execute("PRAGMA table_info(perfil_ia)")}
    if col_perfil and "rasgos" not in col_perfil:
        conn.execute("ALTER TABLE perfil_ia ADD COLUMN rasgos TEXT NOT NULL DEFAULT ''")
    columnas = {f["name"] for f in conn.execute("PRAGMA table_info(cola_salida)")}
    if "ack_estimado_ts" not in columnas:
        conn.execute("ALTER TABLE cola_salida ADD COLUMN ack_estimado_ts TEXT")
    if "resumido" not in columnas:
        conn.execute("ALTER TABLE cola_salida ADD COLUMN resumido INTEGER NOT NULL DEFAULT 0")
    col_tam = {f["name"] for f in conn.execute("PRAGMA table_info(tamizajes)")}
    if "riesgo_autolesion" not in col_tam:
        conn.execute("ALTER TABLE tamizajes ADD COLUMN riesgo_autolesion INTEGER NOT NULL DEFAULT 0")
    if "calidad_oxigeno" not in col_tam:
        conn.execute("ALTER TABLE tamizajes ADD COLUMN calidad_oxigeno REAL")
    if "nivel_protocolo" not in col_tam:
        conn.execute("ALTER TABLE tamizajes ADD COLUMN nivel_protocolo TEXT NOT NULL DEFAULT 'ninguno'")
