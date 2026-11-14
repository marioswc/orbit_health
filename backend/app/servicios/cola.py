"""Casos de uso de la cola de salida y del enlace con Tierra."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio.integridad import GENESIS, calcular_hash, verificar_filas
from ..repositorios import cola as repo
from ..repositorios import enlace as repo_enlace

ENTORNOS = ("marte", "luna")


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def encolar_sin_commit(conn: sqlite3.Connection, tid: str, tipo_evento: str,
                       prioridad: int, payload: dict) -> int:
    """Encola dentro de la transacción abierta por quien llama (debe haber hecho BEGIN IMMEDIATE)."""
    payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    ts = _ahora().isoformat()
    prev = repo.ultimo_hash(conn) or GENESIS
    h = calcular_hash(prev, tid, tipo_evento, prioridad, payload_str, ts)
    return repo.insertar(conn, tid, tipo_evento, prioridad, payload_str, ts, prev, h)


def encolar(conn: sqlite3.Connection, tid: str, tipo_evento: str, prioridad: int, payload: dict) -> int:
    conn.execute("BEGIN IMMEDIATE")
    try:
        evento_id = encolar_sin_commit(conn, tid, tipo_evento, prioridad, payload)
        conn.commit()
        return evento_id
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
    salida = repo.retenidos_ordenados(conn)
    for f in salida:
        repo.marcar_en_transito(conn, f["id"], ahora.isoformat(), llegada.isoformat())
    conn.commit()
    return salida


def actualizar_recibidos(conn: sqlite3.Connection, ahora: datetime | None = None) -> int:
    n = repo.marcar_recibidos(conn, (ahora or _ahora()).isoformat())
    conn.commit()
    return n


def verificar_cadena(conn: sqlite3.Connection) -> dict:
    return verificar_filas(repo.todos_en_orden(conn))


def listar(conn: sqlite3.Connection) -> list[dict]:
    return repo.recientes(conn)


def estado_cola(conn: sqlite3.Connection) -> dict:
    actualizar_recibidos(conn)
    items = listar(conn)
    resumen: dict = {}
    for i in items:
        resumen.setdefault(i["estado"], {1: 0, 2: 0, 3: 0})[i["prioridad"]] += 1
    return {"enlace": repo_enlace.leer(conn), "resumen": resumen, "items": items}


def cambiar_enlace(conn: sqlite3.Connection, activo: bool, entorno: str) -> dict:
    entorno = entorno.lower()
    if entorno not in ENTORNOS:
        raise ValueError("entorno debe ser 'marte' o 'luna'")
    repo_enlace.guardar(conn, activo, entorno)
    conn.commit()
    return {"activo": activo, "entorno": entorno, "despachados": despachar(conn, activo, entorno)}
