"""Lógica de aplicación: registro de lecturas, estado y tamizaje."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from . import config, engine, queue_manager as qm
from .validacion import INDICADORES, NEWS2_VARS, validar

PRIORIDAD = {"rojo": 1, "amarillo": 2, "verde": 3}
AVPU = "AVPU"
_ORDEN = {"verde": 0, "amarillo": 1, "rojo": 2}


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _signos_recientes(conn, tid: str, desde: str) -> dict:
    marcadores = ",".join("?" * len(NEWS2_VARS))
    filas = conn.execute(
        f"""SELECT indicador, valor FROM lecturas
            WHERE tripulante_id=? AND ts>=? AND indicador IN ({marcadores}) ORDER BY id ASC""",
        (tid, desde, *NEWS2_VARS),
    ).fetchall()
    signos: dict = {}
    for f in filas:
        signos[f["indicador"]] = f["valor"]
    return _convertir_avpu(signos)


def _convertir_avpu(signos: dict) -> dict:
    if "avpu" in signos:
        signos = {**signos, "avpu": AVPU[int(signos["avpu"])]}
    return signos


def existe_tripulante(conn, tid: str) -> bool:
    return conn.execute("SELECT 1 FROM tripulantes WHERE id=?", (tid,)).fetchone() is not None


def registrar_lectura(conn: sqlite3.Connection, tid: str, indicador: str, valor: float) -> dict:
    error = validar(indicador, valor)
    if error:
        raise ValueError(error)
    ahora = _ahora()
    ts = ahora.isoformat()
    ventana = (ahora - timedelta(minutes=config.VENTANA_NEWS2_MIN)).isoformat()
    observacion = False
    puntos = 0
    faltantes: list[str] = []

    if indicador in NEWS2_VARS:
        signos = _signos_recientes(conn, tid, ventana)
        signos[indicador] = AVPU[int(valor)] if indicador == "avpu" else valor
        r = engine.evaluar_news2(signos)
        nivel, puntos, faltantes = r.nivel, r.puntos, r.faltantes
    elif indicador == "co2":
        nivel = engine.evaluar_ambiente(co2_mmhg=valor)
    elif indicador == "dosis_pct":
        nivel = engine.evaluar_ambiente(dosis_pct=valor)
    elif indicador == "glucosa":
        nivel, observacion = engine.evaluar_glucosa(valor)
    else:  # presion_diastolica
        nivel, observacion = engine.evaluar_diastolica(valor)

    desde_base = (ahora - timedelta(days=config.DIAS_LINEA_BASE)).isoformat()
    hist = [f["valor"] for f in conn.execute(
        "SELECT valor FROM lecturas WHERE tripulante_id=? AND indicador=? AND ts>=?",
        (tid, indicador, desde_base))]
    base = engine.desviacion_linea_base(valor, hist)
    if base["aviso"] and nivel == "verde":
        nivel = "amarillo"

    unidad = INDICADORES[indicador][1]
    cur = conn.execute(
        """INSERT INTO lecturas (tripulante_id, indicador, valor, unidad, nivel, puntos_news2, origen, ts)
           VALUES (?,?,?,?,?,?, 'manual', ?)""",
        (tid, indicador, valor, unidad, nivel, puntos, ts),
    )
    conn.commit()
    lectura_id = cur.lastrowid
    evento_id = qm.encolar(
        conn, tid, f"LECTURA_{indicador.upper()}", PRIORIDAD[nivel],
        {"lectura_id": lectura_id, "indicador": indicador, "valor": valor,
         "nivel": nivel, "news2": puntos},
    )
    return {"lectura_id": lectura_id, "nivel": nivel, "puntos_news2": puntos,
            "observacion": observacion, "aviso_linea_base": base["aviso"],
            "faltantes_news2": faltantes, "cola_evento_id": evento_id,
            "prioridad": PRIORIDAD[nivel]}


def estado_tripulante(conn: sqlite3.Connection, tid: str) -> dict:
    ahora = _ahora()
    ventana = (ahora - timedelta(minutes=config.VENTANA_NEWS2_MIN)).isoformat()
    filas = conn.execute(
        "SELECT indicador, valor, unidad, nivel, ts FROM lecturas WHERE tripulante_id=? AND ts>=? ORDER BY id ASC",
        (tid, ventana)).fetchall()
    ultimos = {f["indicador"]: dict(f) for f in filas}
    news2 = engine.evaluar_news2(_signos_recientes(conn, tid, ventana))
    peor = max((v["nivel"] for v in ultimos.values()), key=_ORDEN.__getitem__, default="verde")
    return {"indicadores": list(ultimos.values()),
            "news2": {"puntos": news2.puntos, "nivel": news2.nivel, "faltantes": news2.faltantes},
            "nivel_general": peor, "ventana_min": config.VENTANA_NEWS2_MIN}


def registrar_tamizaje(conn, tid: str, item1: int, item2: int) -> dict:
    total = item1 + item2
    conn.execute("INSERT INTO tamizajes (tripulante_id,item1,item2,total) VALUES (?,?,?,?)",
                 (tid, item1, item2, total))
    conn.commit()
    positivo = total >= 3
    capsulas = []
    if positivo:
        capsulas = [dict(c) for c in conn.execute(
            "SELECT id, categoria, titulo, contenido_markdown FROM capsulas WHERE categoria='autorregulacion'")]
    return {"total": total, "positivo": positivo, "capsulas": capsulas, "transmitido_tierra": False}
