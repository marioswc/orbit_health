"""Caso de uso: estado clínico vigente de un tripulante."""
import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio import acciones, combinadas, peligros, reglas
from ..dominio.catalogos import INDICADORES
from ..repositorios import lecturas as repo
from .lecturas import SOLO_ALTA, SOLO_BAJA, signos_recientes


def _redondear(base: dict) -> dict:
    return {k: (round(x, 2) if isinstance(x, float) else x) for k, x in base.items()}


def estado_tripulante(conn: sqlite3.Connection, tid: str, estilo: dict | None = None) -> dict:
    ventana = (datetime.now(timezone.utc) - timedelta(minutes=config.VENTANA_NEWS2_MIN)).isoformat()
    ultimos = repo.ultimas_en_ventana(conn, tid, ventana)
    desde_base = (datetime.now(timezone.utc) - timedelta(days=config.DIAS_LINEA_BASE)).isoformat()
    for v in ultimos:
        previo = repo.historial_previo(conn, tid, v["indicador"], desde_base, v["ts"])
        v["linea_base"] = _redondear(reglas.desviacion_linea_base(v["valor"], previo, solo_baja=v["indicador"] in SOLO_BAJA, solo_alta=v["indicador"] in SOLO_ALTA, piso=reglas.piso_de(v["indicador"])))
    news2 = reglas.evaluar_news2(signos_recientes(conn, tid, ventana))
    valores = repo.valores_recientes(conn, tid, combinadas.INDICADORES_USADOS, ventana)
    activas = combinadas.evaluar_individuales(valores)
    ambientales = ("co2", "o2_cabina", "dosis_pct")
    fisiologico = combinadas.peor_nivel(
        [news2.nivel]
        + [v["nivel"] for v in ultimos if v["indicador"] not in ambientales]
        + [a["nivel"] for a in activas])
    peor = combinadas.peor_nivel(
        [news2.nivel] + [v["nivel"] for v in ultimos] + [a["nivel"] for a in activas])
    estilo = {**acciones.ESTILO_POR_DEFECTO, **(estilo or {})}
    proxima = acciones.ajustar_intervalo(reglas.captura_recomendada_min(peor), peor, estilo["recordatorios"])
    return {"indicadores": ultimos,
            "news2": {"puntos": news2.puntos, "nivel": news2.nivel, "faltantes": news2.faltantes},
            "peligros_relacionados": peligros.peligros_de(
                [v["indicador"] for v in ultimos if v["nivel"] != "verde"]),
            "reglas_combinadas": activas, "nivel_general": peor, "nivel_fisiologico": fisiologico, "ventana_min": config.VENTANA_NEWS2_MIN,
            "proxima_captura_min": proxima,
            "acciones_sugeridas": acciones.acciones_sugeridas(
                peor, proxima, faltantes=news2.faltantes, reglas=activas,
                etiquetas={k: v[0] for k, v in INDICADORES.items()}, tono=estilo["tono"], detalle=estilo["detalle"]),
            "estilo": {k: estilo[k] for k in ("tono", "detalle", "recordatorios")}}
