"""Racha de mediciones: gamificación ligera y sin presión.

Un día cuenta cuando se registraron los 5 signos vitales. La racha actual no se rompe porque hoy todavía no esté
completo: se cuenta hacia atrás desde ayer. No hay castigos ni puntos: solo constancia y unos pocos logros.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone

from ..repositorios import lecturas as repo
from .lecturas import ETIQUETAS

VITALES_DEL_DIA = ("frecuencia_respiratoria", "spo2", "presion_sistolica", "frecuencia_cardiaca", "temperatura")
LOGROS = (("primer_dia", "Primer día completo", 1), ("tres_dias", "Tres días seguidos", 3), ("semana", "Una semana seguida", 7))


def _consecutivos(dias: set[date], fin: date) -> int:
    n = 0
    while fin in dias:
        n += 1
        fin -= timedelta(days=1)
    return n


def racha(conn: sqlite3.Connection, tid: str, ahora: datetime | None = None) -> dict:
    hoy = (ahora or datetime.now(timezone.utc)).date()
    por_dia = repo.indicadores_por_dia(conn, tid, VITALES_DEL_DIA)
    completos = {date.fromisoformat(d) for d, inds in por_dia.items() if set(VITALES_DEL_DIA) <= inds}
    hoy_completo = hoy in completos
    actual = _consecutivos(completos, hoy if hoy_completo else hoy - timedelta(days=1))
    mejor = max((_consecutivos(completos, d) for d in completos), default=0)
    faltan = [ETIQUETAS[i] for i in VITALES_DEL_DIA if i not in por_dia.get(hoy.isoformat(), set())]
    return {"racha_dias": actual, "mejor_racha_dias": mejor, "dias_completos": len(completos),
            "hoy_completo": hoy_completo, "hoy_faltan": faltan,
            "logros": [{"id": i, "nombre": n, "logrado": mejor >= req} for i, n, req in LOGROS],
            "regla": "Un día cuenta cuando se registran los 5 signos vitales; la racha no se rompe mientras el día de hoy esté en curso."}
