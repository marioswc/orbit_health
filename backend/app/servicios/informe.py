"""Informe resumido para entregar a Tierra. Pensado para exportar y para verificar que no se alteró.

Excluye por diseño todo lo personal: diario, tamizajes y ánimo diario nunca forman parte del informe.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sqlite3
from datetime import datetime, timezone

from ..dominio.umbrales import UMBRALES
from ..repositorios import cola as repo_cola
from ..repositorios import enlace as repo_enlace
from ..repositorios import lecturas as repo_lecturas
from ..repositorios import tripulantes
from . import alertas, estado

AVISO = "No incluye diario, tamizajes ni ánimo diario: son privados y nunca salen de la nave."


def _con_hash(cuerpo: dict) -> dict:
    canon = json.dumps(cuerpo, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {**cuerpo, "integridad_sha256": hashlib.sha256(canon.encode("utf-8")).hexdigest()}


def _cabecera() -> dict:
    return {"generado_ts": datetime.now(timezone.utc).isoformat(),
            "umbrales": {"version": UMBRALES["version"], "estado": UMBRALES["estado"]},
            "aviso": AVISO}


def informe_tripulante(conn: sqlite3.Connection, tid: str, limite: int = 50) -> dict:
    f = conn.execute("SELECT id, nombre, rol FROM tripulantes WHERE id=?", (tid,)).fetchone()
    e = estado.estado_tripulante(conn, tid)
    cuerpo = {
        **_cabecera(),
        "tripulante": dict(f),
        "estado": {k: e[k] for k in ("nivel_general", "nivel_fisiologico", "news2", "reglas_combinadas",
                                     "peligros_relacionados", "proxima_captura_min")},
        "indicadores_vigentes": e["indicadores"],
        "lecturas_recientes": repo_lecturas.recientes(conn, tid, max(1, min(limite, 500))),
        "cola_de_salida": repo_cola.conteo_por_estado(conn, tid),
    }
    return _con_hash(cuerpo)


def informe_tripulacion(conn: sqlite3.Connection) -> dict:
    tripulacion = []
    for t in tripulantes.listar(conn):
        e = estado.estado_tripulante(conn, t["id"])
        tripulacion.append({**t, "nivel_general": e["nivel_general"], "nivel_fisiologico": e["nivel_fisiologico"],
                            "news2": e["news2"], "reglas_combinadas": e["reglas_combinadas"]})
    cuerpo = {**_cabecera(), "enlace": repo_enlace.leer(conn), "tripulacion": tripulacion,
              "alertas_colectivas": alertas.alertas_colectivas(conn)["alertas"]}
    return _con_hash(cuerpo)


def lecturas_csv(conn: sqlite3.Connection, tid: str, limite: int = 500) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["ts", "indicador", "valor", "unidad", "nivel", "origen"])
    for r in reversed(repo_lecturas.recientes(conn, tid, max(1, min(limite, 5000)))):
        w.writerow([r["ts"], r["indicador"], r["valor"], r["unidad"], r["nivel"], r["origen"]])
    return buf.getvalue()
