"""Caso de uso: estado clínico vigente de un tripulante."""
import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio import combinadas, reglas
from ..repositorios import lecturas as repo
from .lecturas import signos_recientes


def estado_tripulante(conn: sqlite3.Connection, tid: str) -> dict:
    ventana = (datetime.now(timezone.utc) - timedelta(minutes=config.VENTANA_NEWS2_MIN)).isoformat()
    ultimos = repo.ultimas_en_ventana(conn, tid, ventana)
    news2 = reglas.evaluar_news2(signos_recientes(conn, tid, ventana))
    valores = repo.valores_recientes(conn, tid, combinadas.INDICADORES_USADOS, ventana)
    activas = combinadas.evaluar_individuales(valores)
    ambientales = ("co2", "dosis_pct")
    fisiologico = combinadas.peor_nivel(
        [news2.nivel]
        + [v["nivel"] for v in ultimos if v["indicador"] not in ambientales]
        + [a["nivel"] for a in activas])
    peor = combinadas.peor_nivel(
        [news2.nivel] + [v["nivel"] for v in ultimos] + [a["nivel"] for a in activas])
    return {"indicadores": ultimos,
            "news2": {"puntos": news2.puntos, "nivel": news2.nivel, "faltantes": news2.faltantes},
            "reglas_combinadas": activas, "nivel_general": peor, "nivel_fisiologico": fisiologico, "ventana_min": config.VENTANA_NEWS2_MIN,
            "proxima_captura_min": reglas.captura_recomendada_min(peor)}
