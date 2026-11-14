import sqlite3
from pathlib import Path

from .. import config

SCHEMA = Path(__file__).with_name("schema.sql")


def get_conn(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or config.DB_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
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
    columnas = {f["name"] for f in conn.execute("PRAGMA table_info(cola_salida)")}
    if "ack_estimado_ts" not in columnas:
        conn.execute("ALTER TABLE cola_salida ADD COLUMN ack_estimado_ts TEXT")
