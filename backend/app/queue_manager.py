"""Cola store-and-forward con prioridad y hash encadenado verificable.

hash = SHA-256(hash_prev | tripulante_id | tipo_evento | prioridad | payload | ts_guardado)
Todos los campos, incluido ts_guardado, se persisten, así que la cadena se puede recomputar.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone

from . import config

GENESIS = "GENESIS"


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def calcular_hash(prev: str, tripulante_id: str, tipo_evento: str,
                  prioridad: int, payload: str, ts_guardado: str) -> str:
    base = "|".join([prev, tripulante_id, tipo_evento, str(prioridad), payload, ts_guardado])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


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
    prev = GENESIS
    total = 0
    for f in conn.execute("SELECT * FROM cola_salida ORDER BY id ASC"):
        total += 1
        esperado = calcular_hash(prev, f["tripulante_id"], f["tipo_evento"],
                                 f["prioridad"], f["payload"], f["ts_guardado"])
        if f["hash_prev"] != prev or f["hash"] != esperado:
            return {"valida": False, "total": total, "primer_invalido": f["id"]}
        prev = f["hash"]
    return {"valida": True, "total": total, "primer_invalido": None}


def listar(conn: sqlite3.Connection) -> list[dict]:
    filas = conn.execute(
        """SELECT id, tripulante_id, tipo_evento, prioridad, estado, hash, ts_guardado,
                  transmitido_ts, llegada_estimada_ts
           FROM cola_salida ORDER BY id DESC LIMIT 200"""
    ).fetchall()
    return [dict(f) for f in filas]
