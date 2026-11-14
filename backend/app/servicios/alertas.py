"""Caso de uso: alertas que cruzan a toda la tripulación (CO2 de cabina + estado de los tripulantes)."""
import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio import combinadas
from ..repositorios import lecturas as repo
from ..repositorios import tripulantes
from .estado import estado_tripulante


def alertas_colectivas(conn: sqlite3.Connection) -> dict:
    ventana = (datetime.now(timezone.utc) - timedelta(minutes=config.VENTANA_NEWS2_MIN)).isoformat()
    niveles = {tid: estado_tripulante(conn, tid)["nivel_fisiologico"] for tid in tripulantes.ids(conn)}
    co2 = repo.ultimo_global(conn, "co2", ventana)
    alerta = combinadas.evaluar_colectiva(list(niveles.values()), co2)
    return {"alertas": [alerta] if alerta else [], "co2_mmhg": co2, "niveles": niveles}
