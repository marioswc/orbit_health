"""Caso de uso: estado clínico vigente de un tripulante."""
import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio import reglas
from ..repositorios import lecturas as repo
from .lecturas import signos_recientes

_ORDEN = {"verde": 0, "amarillo": 1, "rojo": 2}


def estado_tripulante(conn: sqlite3.Connection, tid: str) -> dict:
    ventana = (datetime.now(timezone.utc) - timedelta(minutes=config.VENTANA_NEWS2_MIN)).isoformat()
    ultimos = repo.ultimas_en_ventana(conn, tid, ventana)
    news2 = reglas.evaluar_news2(signos_recientes(conn, tid, ventana))
    peor = max((v["nivel"] for v in ultimos), key=_ORDEN.__getitem__, default="verde")
    return {"indicadores": ultimos,
            "news2": {"puntos": news2.puntos, "nivel": news2.nivel, "faltantes": news2.faltantes},
            "nivel_general": peor, "ventana_min": config.VENTANA_NEWS2_MIN,
            "proxima_captura_min": reglas.captura_recomendada_min(peor)}
