"""Dispositivo portátil simulado: genera indicadores plausibles, repetibles con una semilla.

Sirve para probar y demostrar la entrada de sensores sin hardware. Los valores son hipotéticos.
"""
from __future__ import annotations

import random

BASE = {"frecuencia_respiratoria": 16, "spo2": 97, "presion_sistolica": 120, "frecuencia_cardiaca": 70, "temperatura": 36.7}
# Ruido máximo (±) por señal: acotado, para que un perfil estable no salga de su rango normal.
RUIDO = {"frecuencia_respiratoria": 1, "spo2": 1, "presion_sistolica": 3, "frecuencia_cardiaca": 2, "temperatura": 0.1}
# Cambio total a lo largo de la serie (se suma a la base de forma lineal).
DERIVA = {
    "estable": {},
    "deterioro_respiratorio": {"spo2": -9, "frecuencia_respiratoria": 11, "frecuencia_cardiaca": 48,
                               "presion_sistolica": -10, "temperatura": 0.3},
}
DOSIS_RADIACION = {
    "exposicion_radiacion": (68.0, 95.0),
}
PERFILES = tuple((*DERIVA, *DOSIS_RADIACION))


def generar(perfil: str, ticks: int, semilla: int | None = None) -> list[dict[str, float]]:
    """Una lectura de cada signo por 'tick'. Con la misma semilla produce siempre la misma serie."""
    if perfil not in PERFILES:
        raise ValueError(f"perfil debe ser uno de: {', '.join(PERFILES)}")
    if not 1 <= ticks <= 60:
        raise ValueError("ticks debe estar entre 1 y 60")
    rng = random.Random(semilla)
    serie = []
    for i in range(ticks):
        avance = i / (ticks - 1) if ticks > 1 else 0.0
        tick = {}
        for signo, base in BASE.items():
            valor = base + DERIVA.get(perfil, {}).get(signo, 0) * avance + rng.uniform(-RUIDO[signo], RUIDO[signo])
            tick[signo] = round(valor, 1) if signo == "temperatura" else float(round(valor))
        if perfil in DOSIS_RADIACION:
            inicio, fin = DOSIS_RADIACION[perfil]
            tick["dosis_pct"] = round(inicio + (fin - inicio) * avance, 1)
        serie.append(tick)
    return serie
