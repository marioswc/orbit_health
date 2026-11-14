"""Caso de uso: alertas que cruzan a toda la tripulación (CO2 de cabina + estado de los tripulantes)."""
import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio import combinadas, reglas
from ..repositorios import lecturas as repo
from ..repositorios import tripulantes
from .estado import estado_tripulante


def alertas_colectivas(conn: sqlite3.Connection) -> dict:
    ventana = (datetime.now(timezone.utc) - timedelta(minutes=config.VENTANA_NEWS2_MIN)).isoformat()
    niveles = {tid: estado_tripulante(conn, tid)["nivel_fisiologico"] for tid in tripulantes.ids(conn)}
    co2 = repo.ultimo_global(conn, "co2", ventana)
    o2 = repo.ultimo_global(conn, "o2_cabina", ventana)
    alerta_co2 = combinadas.evaluar_colectiva(list(niveles.values()), co2)
    alerta_o2 = combinadas.evaluar_colectiva_o2(list(niveles.values()), o2)
    alertas = [a for a in (alerta_co2, alerta_o2) if a]
    return {
        "alertas": alertas,
        "co2_mmhg": co2,
        "o2_pct": o2,
        "o2_nivel": reglas.evaluar_ambiente(o2_pct=o2) if o2 is not None else None,
        "niveles": niveles,
    }
