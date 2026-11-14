"""Reglas que cruzan señales: individuales (varias lecturas de un tripulante) y colectiva (CO2 + tripulación).

Las condiciones viven en datos/umbrales.json y son supuestos de diseño pendientes de validación clínica.
"""
from __future__ import annotations

import operator
from typing import Mapping, Sequence

from .umbrales import UMBRALES

_OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le}
ORDEN = {"verde": 0, "amarillo": 1, "rojo": 2}
_RC = UMBRALES["reglas_combinadas"]

INDICADORES_USADOS = tuple(sorted({c["indicador"] for r in _RC.get("individuales", []) for c in r["condiciones"]}))


def peor_nivel(niveles: Sequence[str]) -> str:
    return max(niveles, key=ORDEN.__getitem__, default="verde")


def evaluar_individuales(valores: Mapping[str, float], reglas: list[dict] | None = None) -> list[dict]:
    """Devuelve las reglas activas. Una regla solo se activa si tiene dato vigente de todos sus indicadores."""
    activas = []
    for r in (reglas if reglas is not None else _RC.get("individuales", [])):
        if all(c["indicador"] in valores and _OPS[c["op"]](valores[c["indicador"]], c["valor"])
               for c in r["condiciones"]):
            activas.append({"id": r["id"], "nombre": r["nombre"], "nivel": r["nivel"]})
    return activas


def evaluar_colectiva(niveles_tripulantes: Sequence[str], co2_mmhg: float | None,
                      cfg: Mapping | None = None) -> dict | None:
    """Alerta si el CO2 supera el umbral y hay suficientes tripulantes con nivel mínimo o peor."""
    cfg = cfg or _RC.get("colectiva_co2")
    if not cfg or co2_mmhg is None or co2_mmhg <= cfg["co2_sobre"]:
        return None
    afectados = sum(1 for n in niveles_tripulantes if ORDEN[n] >= ORDEN[cfg["nivel_minimo"]])
    if afectados < cfg["min_tripulantes"]:
        return None
    return {"id": cfg["id"], "nombre": cfg["nombre"], "nivel": cfg["nivel"],
            "afectados": afectados, "co2_mmhg": co2_mmhg}
