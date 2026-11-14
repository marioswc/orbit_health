"""Caso de uso: registrar una lectura, clasificarla y encolar su evento (atómico)."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio import reglas
from ..dominio.catalogos import INDICADORES, NEWS2_VARS, validar
from ..repositorios import lecturas as repo
from . import cola

PRIORIDAD = {"rojo": 1, "amarillo": 2, "verde": 3}
AVPU = "AVPU"


def signos_recientes(conn: sqlite3.Connection, tid: str, desde: str) -> dict:
    """Último valor vigente de cada variable NEWS2; AVPU se convierte de 0-3 a letra."""
    signos = repo.valores_recientes(conn, tid, NEWS2_VARS, desde)
    if "avpu" in signos:
        signos["avpu"] = AVPU[int(signos["avpu"])]
    return signos


def _clasificar(conn, tid: str, indicador: str, valor: float, ventana: str) -> dict:
    base = {"nivel": "verde", "puntos": 0, "observacion": False, "faltantes": []}
    if indicador in NEWS2_VARS:
        signos = signos_recientes(conn, tid, ventana)
        signos[indicador] = AVPU[int(valor)] if indicador == "avpu" else valor
        r = reglas.evaluar_news2(signos)
        return {**base, "nivel": r.nivel, "puntos": r.puntos, "faltantes": r.faltantes}
    if indicador == "co2":
        return {**base, "nivel": reglas.evaluar_ambiente(co2_mmhg=valor)}
    if indicador == "dosis_pct":
        return {**base, "nivel": reglas.evaluar_ambiente(dosis_pct=valor)}
    if indicador == "glucosa":
        nivel, obs = reglas.evaluar_glucosa(valor)
    else:  # presion_diastolica
        nivel, obs = reglas.evaluar_diastolica(valor)
    return {**base, "nivel": nivel, "observacion": obs}


def registrar_lectura(conn: sqlite3.Connection, tid: str, indicador: str, valor: float) -> dict:
    error = validar(indicador, valor)
    if error:
        raise ValueError(error)
    ahora = datetime.now(timezone.utc)
    ventana = (ahora - timedelta(minutes=config.VENTANA_NEWS2_MIN)).isoformat()
    desde_base = (ahora - timedelta(days=config.DIAS_LINEA_BASE)).isoformat()

    conn.execute("BEGIN IMMEDIATE")  # lectura y evento de cola: ambos o ninguno
    try:
        c = _clasificar(conn, tid, indicador, valor, ventana)
        linea = reglas.desviacion_linea_base(valor, repo.historial(conn, tid, indicador, desde_base))
        nivel = "amarillo" if linea["aviso"] and c["nivel"] == "verde" else c["nivel"]
        lectura_id = repo.insertar(conn, tid, indicador, valor, INDICADORES[indicador][1],
                                   nivel, c["puntos"], ahora.isoformat())
        evento_id = cola.encolar_sin_commit(
            conn, tid, f"LECTURA_{indicador.upper()}", PRIORIDAD[nivel],
            {"lectura_id": lectura_id, "indicador": indicador, "valor": valor,
             "nivel": nivel, "news2": c["puntos"]})
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"lectura_id": lectura_id, "nivel": nivel, "puntos_news2": c["puntos"],
            "observacion": c["observacion"], "aviso_linea_base": linea["aviso"],
            "faltantes_news2": c["faltantes"], "cola_evento_id": evento_id,
            "prioridad": PRIORIDAD[nivel],
            "proxima_captura_min": reglas.captura_recomendada_min(nivel)}
