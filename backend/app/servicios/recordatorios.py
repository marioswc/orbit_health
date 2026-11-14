"""Recordatorios de medición: quién está al día y quién tiene la captura vencida.

El intervalo sale del nivel actual de cada tripulante (más corto si está peor) y de la frecuencia de
recordatorios que él mismo eligió. Solo calcula y avisa: no bloquea nada ni cambia ningún nivel.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from ..repositorios import lecturas as repo_lecturas
from ..repositorios import tripulantes
from . import estado, preferencias


def _minutos(desde_iso: str, ahora: datetime) -> float:
    return (ahora - datetime.fromisoformat(desde_iso)).total_seconds() / 60


def recordatorio_tripulante(conn: sqlite3.Connection, tid: str, nombre: str = "", ahora: datetime | None = None) -> dict:
    ahora = ahora or datetime.now(timezone.utc)
    e = estado.estado_tripulante(conn, tid, preferencias.obtener(conn, tid))
    intervalo = e["proxima_captura_min"]
    ultima = repo_lecturas.ultima_captura(conn, tid)
    if ultima is None:
        vencido, desde, restante = True, None, None
    else:
        desde = round(_minutos(ultima, ahora), 1)
        restante = round(intervalo - desde, 1)
        vencido = restante < 0
    return {"tripulante_id": tid, "nombre": nombre, "nivel_general": e["nivel_general"],
            "intervalo_min": intervalo, "ultima_captura_ts": ultima, "minutos_desde_ultima": desde,
            "vencido": vencido, "sin_capturas": ultima is None,
            "atrasado_min": round(-restante, 1) if vencido and restante is not None else 0.0,
            "faltan_en_min": round(restante, 1) if restante is not None and not vencido else 0.0,
            "faltantes_news2": e["news2"]["faltantes"]}


def recordatorios_tripulacion(conn: sqlite3.Connection, ahora: datetime | None = None) -> dict:
    """Todos los tripulantes, con los vencidos primero y el más atrasado a la cabeza."""
    ahora = ahora or datetime.now(timezone.utc)
    filas = [recordatorio_tripulante(conn, t["id"], t["nombre"], ahora) for t in tripulantes.listar(conn)]
    filas.sort(key=lambda r: (not r["vencido"], not r["sin_capturas"], -r["atrasado_min"], r["tripulante_id"]))
    return {"timestamp": ahora.isoformat(), "vencidos": sum(1 for r in filas if r["vencido"]), "tripulacion": filas}
