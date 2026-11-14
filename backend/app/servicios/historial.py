"""Caso de uso: serie temporal de un indicador para las gráficas del frontend."""
import sqlite3
import statistics
from datetime import datetime, timedelta, timezone

from ..dominio.catalogos import INDICADORES
from ..repositorios import lecturas as repo


def serie_indicador(conn: sqlite3.Connection, tid: str, indicador: str, dias: float = 14, limite: int = 500) -> dict:
    if indicador not in INDICADORES:
        raise ValueError(f"Indicador desconocido: {indicador}")
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
    puntos = repo.serie(conn, tid, indicador, desde, max(1, min(limite, 2000)))
    valores = [p["valor"] for p in puntos]
    resumen = {"n": len(valores)}
    if valores:
        resumen |= {"min": min(valores), "max": max(valores), "media": round(statistics.fmean(valores), 2)}
    return {"indicador": indicador, "etiqueta": INDICADORES[indicador][0], "unidad": INDICADORES[indicador][1],
            "dias": dias, "puntos": puntos, "resumen": resumen}
