"""Reglas puras para un flujo continuo de sensores: qué es un valor extremo y cómo se resume una ventana.

Una banda envía una muestra por segundo. Guardar cada una inundaría la base y la cola de salida, así que se
resumen en una ventana de tiempo (mediana). La excepción son los valores extremos, que no esperan a la ventana.
"""
from __future__ import annotations

import statistics
from typing import Sequence

from . import reglas

VARIABLES_NEWS2 = ("frecuencia_respiratoria", "spo2", "presion_sistolica", "frecuencia_cardiaca", "temperatura")


def es_extremo(indicador: str, valor: float) -> bool:
    """Un valor extremo es el que, por sí solo, ya sería rojo. No debe esperar a que cierre una ventana."""
    if indicador in VARIABLES_NEWS2:
        return bool(reglas.evaluar_news2({indicador: valor}).extremos)
    if indicador == "avpu":
        return int(valor) > 0                       # cualquier cambio de conciencia es urgente
    if indicador == "co2":
        return reglas.evaluar_ambiente(co2_mmhg=valor) == "rojo"
    if indicador == "dosis_pct":
        return reglas.evaluar_ambiente(dosis_pct=valor) == "rojo"
    if indicador == "glucosa":
        return reglas.evaluar_glucosa(valor)[0] == "rojo"
    if indicador == "o2_cabina":
        return reglas.evaluar_o2_cabina(valor) == "rojo"
    return False


def resumir(valores: Sequence[float]) -> float:
    """La mediana resiste lecturas sueltas erróneas (un artefacto de movimiento no cambia el resumen)."""
    return float(statistics.median(valores))
