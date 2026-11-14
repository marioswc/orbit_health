"""Casos de uso de la cola de salida y del enlace con Tierra."""
from __future__ import annotations

import json
import random
import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio import enlace as modelo_enlace
from ..dominio.integridad import GENESIS, calcular_hash, verificar_filas
from ..repositorios import cola as repo
from ..repositorios import enlace as repo_enlace

_RNG = random.Random(int(config.JITTER_SEMILLA)) if config.JITTER_SEMILLA else random.Random()


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
    """Retardo unidireccional simulado (con jitter opcional) en segundos de reloj de pared."""
    real = modelo_enlace.con_jitter(modelo_enlace.retardo_base_s(entorno), config.JITTER_PCT, _RNG)
    return real / config.FACTOR_ACELERACION


def despachar_sin_commit(conn: sqlite3.Connection, enlace_activo: bool, entorno: str = "marte",
                         ahora: datetime | None = None) -> list[dict]:
    """Con enlace activo drena por prioridad (1→3) y antigüedad dentro de la transacción activa."""
    if not enlace_activo:
        return []
    ahora = ahora or _ahora()
    retardo = latencia_s(entorno)
    llegada = ahora + timedelta(seconds=retardo)
    ack = ahora + timedelta(seconds=2 * retardo)  # la confirmación vuelve por el mismo enlace
    salida = repo.retenidos_ordenados(conn)
    for f in salida:
        repo.marcar_en_transito(conn, f["id"], ahora.isoformat(), llegada.isoformat(), ack.isoformat())
    return salida


def despachar_si_activo(conn: sqlite3.Connection, ahora: datetime | None = None) -> list[dict]:
    """Si el enlace persistido está activo, despacha los eventos retenidos sin hacer commit."""
    enlace = repo_enlace.leer(conn)
    return despachar_sin_commit(conn, enlace["activo"], enlace["entorno"], ahora)


def despachar(conn: sqlite3.Connection, enlace_activo: bool, entorno: str = "marte",
              ahora: datetime | None = None) -> list[dict]:
    """Con enlace activo drena por prioridad (1→3) y antigüedad. En eclipse no sale nada."""
    salida = despachar_sin_commit(conn, enlace_activo, entorno, ahora)
    conn.commit()
    return salida


def actualizar_recibidos(conn: sqlite3.Connection, ahora: datetime | None = None) -> int:
    n = repo.marcar_recibidos(conn, (ahora or _ahora()).isoformat())
    conn.commit()
    return n


def verificar_cadena(conn: sqlite3.Connection) -> dict:
    return verificar_filas(repo.todos_en_orden(conn))


def listar(conn: sqlite3.Connection, ahora: datetime | None = None) -> list[dict]:
    """Eventos recientes. `confirmado` indica que la confirmación de Tierra ya volvió a la nave."""
    ahora_iso = (ahora or _ahora()).isoformat()
    items = repo.recientes(conn)
    for i in items:
        i["confirmado"] = bool(i.get("ack_estimado_ts") and i["ack_estimado_ts"] <= ahora_iso)
    return items


def estado_cola(conn: sqlite3.Connection) -> dict:
    actualizar_recibidos(conn)
    items = listar(conn)
    resumen: dict = {}
    for i in items:
        resumen.setdefault(i["estado"], {1: 0, 2: 0, 3: 0})[i["prioridad"]] += 1
    return {"enlace": repo_enlace.leer(conn), "resumen": resumen, "items": items}


def cambiar_enlace(conn: sqlite3.Connection, activo: bool, entorno: str) -> dict:
    entorno = entorno.lower()
    if entorno not in modelo_enlace.entornos():
        raise ValueError(f"entorno debe ser uno de: {', '.join(modelo_enlace.entornos())}")
    repo_enlace.guardar(conn, activo, entorno)
    conn.commit()
    return {"activo": activo, "entorno": entorno, "despachados": despachar(conn, activo, entorno)}


def info_latencia(conn: sqlite3.Connection) -> dict:
    """Parámetros vigentes del modelo de enlace, para mostrarlos en la consola."""
    actual = repo_enlace.leer(conn)
    base = modelo_enlace.retardo_base_s(actual["entorno"])
    factor = config.FACTOR_ACELERACION
    en_transito = [i for i in listar(conn) if i["estado"] == "en_transito"]
    llegadas = sorted(i["llegada_estimada_ts"] for i in en_transito if i["llegada_estimada_ts"])
    return {
        "enlace": actual,
        "perfiles": {k: {"nombre": v["nombre"], "retardo_s": v["retardo_s"]} for k, v in modelo_enlace.PERFILES.items()},
        "factor_aceleracion": factor,
        "jitter_pct": config.JITTER_PCT,
        "retardo_real_s": base,
        "retardo_simulado_s": round(base / factor, 3),
        "ida_y_vuelta_real_s": 2 * base,
        "ida_y_vuelta_simulada_s": round(2 * base / factor, 3),
        "en_transito": len(en_transito),
        "proxima_llegada_ts": llegadas[0] if llegadas else None,
        "estado_modelo": modelo_enlace.DATOS["estado"],
    }
