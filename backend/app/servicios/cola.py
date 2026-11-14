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
PASO_DESPACHO_S = 1.0  # desfase de serialización entre eventos al drenar cola por prioridad


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
    return real / modelo_enlace.factor_valido(config.FACTOR_ACELERACION)


def _calcular_tramo(entorno: str, tx: datetime,
                    llegada_prev: datetime | None, ack_prev: datetime | None) -> tuple[datetime, datetime]:
    """Calcula llegada y confirmación garantizando que respeten el orden de prioridad del lote."""
    retardo_ida = latencia_s(entorno)
    retardo_vuelta = latencia_s(entorno) if config.JITTER_PCT > 0 else retardo_ida
    llegada = tx + timedelta(seconds=retardo_ida)
    if llegada_prev is not None and llegada <= llegada_prev:
        llegada = llegada_prev + timedelta(milliseconds=1)
    ack = llegada + timedelta(seconds=retardo_vuelta)
    if ack_prev is not None and ack <= ack_prev:
        ack = ack_prev + timedelta(milliseconds=1)
    return llegada, ack


def despachar_sin_commit(conn: sqlite3.Connection, enlace_activo: bool, entorno: str = "marte",
                         ahora: datetime | None = None) -> list[dict]:
    """Con enlace activo drena por prioridad (1→3) y antigüedad dentro de la transacción activa."""
    if not enlace_activo:
        return []
    ahora = ahora or _ahora()
    salida = repo.retenidos_ordenados(conn)
    llegada_prev: datetime | None = None
    ack_prev: datetime | None = None
    for idx, f in enumerate(salida):
        tx = ahora + timedelta(seconds=idx * PASO_DESPACHO_S)
        llegada, ack = _calcular_tramo(entorno, tx, llegada_prev, ack_prev)
        repo.marcar_en_transito(conn, f["id"], tx.isoformat(), llegada.isoformat(), ack.isoformat())
        llegada_prev, ack_prev = llegada, ack
    return salida


def _recalcular_en_transito(conn: sqlite3.Connection, entorno: str, ahora: datetime) -> None:
    """Ajusta los tiempos estimados de eventos en tránsito al cambiar de perfil de enlace."""
    en_vuelo = repo.en_transito_ordenados(conn)
    llegada_prev: datetime | None = None
    ack_prev: datetime | None = None
    for idx, f in enumerate(en_vuelo):
        tx_base = datetime.fromisoformat(f["transmitido_ts"]) if f.get("transmitido_ts") else ahora
        tx = tx_base + timedelta(seconds=idx * PASO_DESPACHO_S) if idx > 0 and tx_base == ahora else tx_base
        llegada, ack = _calcular_tramo(entorno, tx, llegada_prev, ack_prev)
        repo.marcar_en_transito(conn, f["id"], tx.isoformat(), llegada.isoformat(), ack.isoformat())
        llegada_prev, ack_prev = llegada, ack
    repo.marcar_recibidos(conn, ahora.isoformat())


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
        i["confirmado"] = bool(
            i["estado"] == "recibido" and i.get("ack_estimado_ts") and i["ack_estimado_ts"] <= ahora_iso
        )
    return items


def estado_cola(conn: sqlite3.Connection, ahora: datetime | None = None) -> dict:
    ahora = ahora or _ahora()
    actualizar_recibidos(conn, ahora)
    items = listar(conn, ahora)
    resumen: dict = {}
    for f in repo.conteo_por_estado_y_prioridad(conn):
        resumen.setdefault(f["estado"], {1: 0, 2: 0, 3: 0})[f["prioridad"]] = f["total"]
    return {"enlace": repo_enlace.leer(conn), "resumen": resumen, "items": items}


def cambiar_enlace(conn: sqlite3.Connection, activo: bool, entorno: str,
                   ahora: datetime | None = None) -> dict:
    entorno = entorno.lower()
    if entorno not in modelo_enlace.entornos():
        raise ValueError(f"entorno debe ser uno de: {', '.join(modelo_enlace.entornos())}")
    ahora = ahora or _ahora()
    if not conn.in_transaction:
        conn.execute("BEGIN IMMEDIATE")
    try:
        previo = repo_enlace.leer(conn)
        repo.marcar_recibidos(conn, ahora.isoformat())
        repo_enlace.guardar(conn, activo, entorno)
        if activo and previo["entorno"] != entorno:
            _recalcular_en_transito(conn, entorno, ahora)
        despachados = despachar_sin_commit(conn, activo, entorno, ahora)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"activo": activo, "entorno": entorno, "despachados": despachados}


def info_latencia(conn: sqlite3.Connection, ahora: datetime | None = None) -> dict:
    """Parámetros vigentes del modelo de enlace, para mostrarlos en la consola."""
    ahora = ahora or _ahora()
    actualizar_recibidos(conn, ahora)
    actual = repo_enlace.leer(conn)
    base = modelo_enlace.retardo_base_s(actual["entorno"])
    factor = modelo_enlace.factor_valido(config.FACTOR_ACELERACION)
    en_transito = repo.en_transito_ordenados(conn)
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
