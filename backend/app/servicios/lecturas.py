"""Caso de uso: registrar una lectura, clasificarla y encolar su evento (atómico)."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio import acciones, combinadas, peligros, reglas
from ..dominio.umbrales import UMBRALES
from ..dominio.catalogos import INDICADORES, NEWS2_VARS, validar
from ..repositorios import lecturas as repo
from . import cola

PRIORIDAD = {"rojo": 1, "amarillo": 2, "verde": 3}
_ORDEN = {"verde": 0, "amarillo": 1, "rojo": 2}
AVPU = "AVPU"
ETIQUETAS = {k: v[0] for k, v in INDICADORES.items()}
# Indicadores donde tener MÁS de lo habitual no es un problema: solo avisa la desviación hacia abajo.
SOLO_BAJA = {"sueno_horas", "ejercicio_min"}


def signos_recientes(conn: sqlite3.Connection, tid: str, desde: str) -> dict:
    """Último valor vigente de cada variable NEWS2; AVPU se convierte de 0-3 a letra."""
    signos = repo.valores_recientes(conn, tid, NEWS2_VARS, desde)
    if "avpu" in signos:
        signos["avpu"] = AVPU[int(signos["avpu"])]
    return signos


def _clasificar(conn, tid: str, indicador: str, valor: float, ventana: str) -> dict:
    base = {"nivel": "verde", "nivel_global": "verde", "puntos": 0, "puntos_ind": 0,
            "observacion": False, "faltantes": []}
    if indicador in NEWS2_VARS:
        val_norm = AVPU[int(valor)] if indicador == "avpu" else valor
        r_ind = reglas.evaluar_news2({indicador: val_norm})
        signos = signos_recientes(conn, tid, ventana)
        signos[indicador] = val_norm
        r_global = reglas.evaluar_news2(signos)
        return {**base, "nivel": r_ind.nivel, "nivel_global": r_global.nivel,
                "puntos": r_global.puntos, "puntos_ind": r_ind.puntos,
                "faltantes": r_global.faltantes}
    if indicador == "co2":
        nivel = reglas.evaluar_ambiente(co2_mmhg=valor)
        return {**base, "nivel": nivel, "nivel_global": nivel}
    if indicador == "o2_cabina":
        nivel = reglas.evaluar_ambiente(o2_pct=valor)
        return {**base, "nivel": nivel, "nivel_global": nivel}
    if indicador == "dosis_pct":
        nivel = reglas.evaluar_ambiente(dosis_pct=valor)
        return {**base, "nivel": nivel, "nivel_global": nivel}
    if indicador == "glucosa":
        nivel, obs = reglas.evaluar_glucosa(valor)
    elif indicador == "sueno_horas":
        nivel, obs = reglas.evaluar_sueno(valor)
    elif indicador == "ejercicio_min":
        nivel, obs = "verde", False        # sin umbral absoluto: solo cuenta la comparación con la propia base
    else:  # presion_diastolica
        nivel, obs = reglas.evaluar_diastolica(valor)
    return {**base, "nivel": nivel, "nivel_global": nivel, "observacion": obs}


def registrar_lectura(conn: sqlite3.Connection, tid: str, indicador: str, valor: float,
                      estilo: dict | None = None, origen: str = "manual") -> dict:
    error = validar(indicador, valor)
    if error:
        raise ValueError(error)
    ahora = datetime.now(timezone.utc)
    ventana = (ahora - timedelta(minutes=config.VENTANA_NEWS2_MIN)).isoformat()
    desde_base = (ahora - timedelta(days=config.DIAS_LINEA_BASE)).isoformat()

    conn.execute("BEGIN IMMEDIATE")  # lectura y evento de cola: ambos o ninguno
    try:
        c = _clasificar(conn, tid, indicador, valor, ventana)
        linea = reglas.desviacion_linea_base(valor, repo.historial(conn, tid, indicador, desde_base),
                                             solo_baja=indicador in SOLO_BAJA, piso=reglas.piso_de(indicador))
        nivel_lectura = "amarillo" if linea["aviso"] and c["nivel"] == "verde" else c["nivel"]
        nivel_evento = (max(nivel_lectura, c["nivel_global"], key=_ORDEN.__getitem__)
                        if c["puntos_ind"] > 0 else nivel_lectura)
        valores = repo.valores_recientes(conn, tid, combinadas.INDICADORES_USADOS, ventana)
        valores[indicador] = valor
        activas = combinadas.evaluar_individuales(valores)
        nivel_evento = combinadas.peor_nivel([nivel_evento, *[a["nivel"] for a in activas]])
        lectura_id = repo.insertar(conn, tid, indicador, valor, INDICADORES[indicador][1],
                                   nivel_lectura, c["puntos"], ahora.isoformat(), origen)
        evento_id = cola.encolar_sin_commit(
            conn, tid, f"LECTURA_{indicador.upper()}", PRIORIDAD[nivel_evento],
            {"lectura_id": lectura_id, "indicador": indicador, "valor": valor,
             "nivel": nivel_evento, "news2": c["puntos"], "reglas": [a["id"] for a in activas],
             "reglas_version": UMBRALES["version"], "reglas_estado": UMBRALES["estado"], "origen": origen})
        cola.despachar_si_activo(conn, ahora)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    estilo = {**acciones.ESTILO_POR_DEFECTO, **(estilo or {})}
    proxima = acciones.ajustar_intervalo(reglas.captura_recomendada_min(nivel_evento), nivel_evento, estilo["recordatorios"])
    return {"lectura_id": lectura_id, "nivel": nivel_evento,
            "acciones_sugeridas": acciones.acciones_sugeridas(
                nivel_evento, proxima, c["observacion"], linea["aviso"], c["faltantes"], activas, ETIQUETAS,
                estilo["tono"], estilo["detalle"]),
            "estilo": {k: estilo[k] for k in ("tono", "detalle", "recordatorios")}, "puntos_news2": c["puntos"],
            "observacion": c["observacion"], "aviso_linea_base": linea["aviso"],
            "peligros_relacionados": peligros.peligros_de([indicador]) if nivel_evento != "verde" else [],
            "faltantes_news2": c["faltantes"], "reglas_combinadas": activas, "cola_evento_id": evento_id,
            "prioridad": PRIORIDAD[nivel_evento],
            "proxima_captura_min": proxima}
