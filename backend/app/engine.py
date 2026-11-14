"""Motor clínico determinista: NEWS2, ambiente y línea base personal.

Los umbrales de ambiente y línea base son supuestos de diseño pendientes de
validación médica (ver PLAN_DE_DESARROLLO.md, secciones 6.2 y 6.3).
"""
from __future__ import annotations

import os
import statistics
from dataclasses import dataclass, field
from typing import Mapping, Sequence

# "conservador": un parámetro aislado en 3 puntos es rojo (adaptación propia).
# "rcp": un parámetro aislado en 3 puntos es amarillo (esquema RCP).
MODO_PARAMETRO_EXTREMO = os.getenv("ORBIT_MODO_PARAMETRO_EXTREMO", "conservador")

MIN_MUESTRAS_BASE = 5  # Supuesto
K_DESVIACIONES = 2.0


@dataclass
class ResultadoNews2:
    puntos: int
    nivel: str
    desglose: dict[str, int] = field(default_factory=dict)
    extremos: list[str] = field(default_factory=list)
    faltantes: list[str] = field(default_factory=list)


def _fr(v: float) -> int:
    if v <= 8 or v >= 25:
        return 3
    if v >= 21:
        return 2
    if v <= 11:
        return 1
    return 0


def _spo2(v: float) -> int:
    if v <= 91:
        return 3
    if v <= 93:
        return 2
    if v <= 95:
        return 1
    return 0


def _pas(v: float) -> int:
    if v <= 90 or v >= 220:
        return 3
    if v <= 100:
        return 2
    if v <= 110:
        return 1
    return 0


def _fc(v: float) -> int:
    if v <= 40 or v >= 131:
        return 3
    if v >= 111:
        return 2
    if v <= 50 or v >= 91:
        return 1
    return 0


def _avpu(v: str) -> int:
    return 0 if str(v).upper() == "A" else 3


def _temp(v: float) -> int:
    if v <= 35.0:
        return 3
    if v <= 36.0:
        return 1
    if v <= 38.0:
        return 0
    if v <= 39.0:
        return 1
    return 2


_REGLAS = {
    "frecuencia_respiratoria": _fr,
    "spo2": _spo2,
    "presion_sistolica": _pas,
    "frecuencia_cardiaca": _fc,
    "avpu": _avpu,
    "temperatura": _temp,
}


def evaluar_news2(signos: Mapping[str, float | str]) -> ResultadoNews2:
    """Puntúa las variables presentes. Las ausentes suman 0 y se reportan en `faltantes`."""
    desglose: dict[str, int] = {}
    faltantes: list[str] = []
    for nombre, regla in _REGLAS.items():
        valor = signos.get(nombre)
        if valor is None:
            faltantes.append(nombre)
        else:
            desglose[nombre] = regla(valor)

    puntos = sum(desglose.values())
    extremos = [n for n, p in desglose.items() if p == 3]

    if puntos >= 7:
        nivel = "rojo"
    elif extremos:
        nivel = "rojo" if MODO_PARAMETRO_EXTREMO == "conservador" else "amarillo"
    elif puntos >= 5:
        nivel = "amarillo"
    else:
        nivel = "verde"
    return ResultadoNews2(puntos, nivel, desglose, extremos, faltantes)


def evaluar_ambiente(co2_mmhg: float | None = None, dosis_pct: float | None = None) -> str:
    """Peor nivel entre CO2 y dosis acumulada (% del límite de misión)."""
    niveles = ["verde"]
    if co2_mmhg is not None:
        niveles.append("rojo" if co2_mmhg > 4.0 else "amarillo" if co2_mmhg > 3.0 else "verde")
    if dosis_pct is not None:
        niveles.append("rojo" if dosis_pct >= 90 else "amarillo" if dosis_pct >= 70 else "verde")
    orden = {"verde": 0, "amarillo": 1, "rojo": 2}
    return max(niveles, key=orden.__getitem__)


def desviacion_linea_base(valor: float, historial: Sequence[float]) -> dict:
    """Compara `valor` con media y DE muestral del historial (últimos 14 días)."""
    n = len(historial)
    if n < MIN_MUESTRAS_BASE:
        return {"aplica": False, "n": n, "aviso": False}
    mu = statistics.fmean(historial)
    sigma = statistics.stdev(historial)
    if sigma == 0:
        aviso = valor != mu
        z = None
    else:
        z = (valor - mu) / sigma
        aviso = abs(z) > K_DESVIACIONES
    return {"aplica": True, "n": n, "media": mu, "desviacion": sigma, "z": z, "aviso": aviso}


def evaluar_glucosa(mg_dl: float) -> tuple[str, bool]:
    """Devuelve (nivel, observacion). Supuesto: umbrales de diseño pendientes de validación médica."""
    if mg_dl < 54 or mg_dl >= 300:
        return "rojo", False
    if mg_dl < 70 or mg_dl >= 126:
        return "amarillo", False
    return "verde", 100 <= mg_dl <= 125


def evaluar_diastolica(mmhg: float) -> tuple[str, bool]:
    """Supuesto: <60 mmHg se marca como observación de perfusión, no como alerta."""
    return "verde", mmhg < 60
