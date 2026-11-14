"""Cola store-and-forward con prioridad. El hash encadenado vive en dominio/integridad.py."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

from . import config
from .dominio.integridad import GENESIS, calcular_hash, verificar_filas


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def encolar(conn: sqlite3.Connection, tripulante_id: str, tipo_evento: str,
            prioridad: int, payload: dict) -> int:
    payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    ts = _ahora().isoformat()
    conn.execute("BEGIN IMMEDIATE")
    try:
        fila = conn.execute("SELECT hash FROM cola_salida ORDER BY id DESC LIMIT 1").fetchone()
        prev = fila["hash"] if fila else GENESIS
        h = calcular_hash(prev, tripulante_id, tipo_evento, prioridad, payload_str, ts)
        cur = conn.execute(
            """INSERT INTO cola_salida
               (tripulante_id, tipo_evento, prioridad, payload, ts_guardado, hash_prev, hash)
               VALUES (?,?,?,?,?,?,?)""",
            (tripulante_id, tipo_evento, prioridad, payload_str, ts, prev, h),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise


def latencia_s(entorno: str) -> float:
    base = config.LATENCIA_MARTE_S if entorno.lower() == "marte" else config.LATENCIA_LUNA_S
    return base / config.FACTOR_ACELERACION


def despachar(conn: sqlite3.Connection, enlace_activo: bool, entorno: str = "marte",
              ahora: datetime | None = None) -> list[dict]:
    """Con enlace activo drena por prioridad (1→3) y antigüedad. En eclipse no sale nada."""
    if not enlace_activo:
        return []
    ahora = ahora or _ahora()
    llegada = ahora + timedelta(seconds=latencia_s(entorno))
    filas = conn.execute(
        """SELECT id, tripulante_id, tipo_evento, prioridad FROM cola_salida
           WHERE estado='retenido' ORDER BY prioridad ASC, id ASC"""
    ).fetchall()
    salida = []
    for f in filas:
        conn.execute(
            """UPDATE cola_salida SET estado='en_transito', transmitido_ts=?, llegada_estimada_ts=?
               WHERE id=?""",
            (ahora.isoformat(), llegada.isoformat(), f["id"]),
        )
        salida.append(dict(f))
    conn.commit()
    return salida


def actualizar_recibidos(conn: sqlite3.Connection, ahora: datetime | None = None) -> int:
    ahora = ahora or _ahora()
    cur = conn.execute(
        "UPDATE cola_salida SET estado='recibido' WHERE estado='en_transito' AND llegada_estimada_ts<=?",
        (ahora.isoformat(),),
    )
    conn.commit()
    return cur.rowcount


def verificar_cadena(conn: sqlite3.Connection) -> dict:
    return verificar_filas(conn.execute("SELECT * FROM cola_salida ORDER BY id ASC"))


def listar(conn: sqlite3.Connection) -> list[dict]:
    filas = conn.execute(
        """SELECT id, tripulante_id, tipo_evento, prioridad, estado, hash, ts_guardado,
                  transmitido_ts, llegada_estimada_ts
           FROM cola_salida ORDER BY id DESC LIMIT 200"""
    ).fetchall()
    return [dict(f) for f in filas]
