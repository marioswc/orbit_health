"""Registro de auditoría encadenado con hash: quién hizo qué, verificable sin red."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from ..dominio.integridad import GENESIS, calcular_hash, verificar_filas
from ..repositorios import seguridad as repo


def registrar(conn: sqlite3.Connection, actor: str | None, accion: str,
              objetivo: str | None = None, detalle: dict | None = None) -> int:
    """Agrega un evento dentro de la transacción actual (quien llama hace commit)."""
    payload = json.dumps({"objetivo": objetivo, "detalle": detalle or {}}, sort_keys=True, separators=(",", ":"))
    ts = datetime.now(timezone.utc).isoformat()
    actor = actor or "sistema"
    prev = repo.auditoria_ultimo_hash(conn) or GENESIS
    h = calcular_hash(prev, actor, accion, 0, payload, ts)
    return repo.auditoria_insertar(conn, actor, accion, payload, ts, prev, h)


def verificar(conn: sqlite3.Connection) -> dict:
    return verificar_filas(repo.auditoria_todos(conn))


def recientes(conn: sqlite3.Connection, limite: int = 100) -> list[dict]:
    return repo.auditoria_recientes(conn, limite)


def anotar(actor: str | None, accion: str, objetivo: str | None = None, detalle: dict | None = None) -> None:
    """Registra un evento con su propia conexión y transacción (sirve desde cualquier hilo o punto de la app). Nunca lanza:
    un fallo de auditoría no debe tumbar la función que se está auditando. NO pasar texto de usuarios en `detalle`."""
    from ..repositorios.conexion import get_conn
    conn = None
    try:
        conn = get_conn()
        conn.execute("BEGIN IMMEDIATE")
        registrar(conn, actor, accion, objetivo, detalle)
        conn.commit()
    except Exception:                                   # noqa: BLE001
        if conn is not None:
            try:
                conn.rollback()
            except Exception:                           # noqa: BLE001
                pass
    finally:
        if conn is not None:
            conn.close()
