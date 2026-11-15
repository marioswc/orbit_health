"""Reglas clínicas deterministas: NEWS2, ambiente, glucosa, diastólica y línea base personal.

Los umbrales se leen de datos/umbrales.json (supuestos de diseño pendientes de validación médica).
"""
from __future__ import annotations

import os
import statistics
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .umbrales import UMBRALES

_N2 = UMBRALES["news2"]
_AMB = UMBRALES["ambiente"]
_GLU = UMBRALES["glucosa_mg_dl"]
_LB = UMBRALES["linea_base"]

# "conservador": un parámetro aislado en 3 puntos es rojo (adaptación propia).
# "rcp": un parámetro aislado en 3 puntos es amarillo (esquema RCP).
MODO_PARAMETRO_EXTREMO = os.getenv("ORBIT_MODO_PARAMETRO_EXTREMO") or _N2["modo_parametro_extremo"]

MIN_MUESTRAS_BASE = _LB["min_muestras"]
K_DESVIACIONES = _LB["desviaciones"]
_ORDEN = {"verde": 0, "amarillo": 1, "rojo": 2}
_ESTADO_SEMAFORO = {
    "verde": "sin_alerta",
    "amarillo": "seguimiento",
    "rojo": "urgente",
}


@dataclass
class ResultadoNews2:
    puntos: int
    nivel: str
    desglose: dict[str, int] = field(default_factory=dict)
    extremos: list[str] = field(default_factory=list)
    faltantes: list[str] = field(default_factory=list)


def estado_semaforo(nivel: str, observacion: bool = False) -> str:
    """Explica el semáforo operativo sin convertirlo en un diagnóstico."""
    if nivel not in _ESTADO_SEMAFORO:
        raise ValueError(f"nivel desconocido: {nivel}")
    if nivel == "verde" and observacion:
        return "observacion"
    return _ESTADO_SEMAFORO[nivel]


def _puntos_por_bandas(bandas: list[dict], valor: float) -> int:
    for b in bandas[:-1]:
        if valor <= b["hasta"]:
            return b["puntos"]
    return bandas[-1]["puntos"]


def _avpu(valor: str) -> int:
    tabla = _N2["avpu"]
    return tabla.get(str(valor).upper(), tabla["otro"])


def _puntaje(variable: str, valor) -> int:
    if variable == "avpu":
        return _avpu(valor)
    return _puntos_por_bandas(_N2["bandas"][variable], valor)


VARIABLES_NEWS2 = ("frecuencia_respiratoria", "spo2", "presion_sistolica",
                   "frecuencia_cardiaca", "avpu", "temperatura")


def evaluar_news2(signos: Mapping[str, float | str]) -> ResultadoNews2:
    """Puntúa las variables presentes. Las ausentes suman 0 y se reportan en `faltantes`."""
    desglose: dict[str, int] = {}
    faltantes: list[str] = []
    for variable in VARIABLES_NEWS2:
        valor = signos.get(variable)
        if valor is None:
            faltantes.append(variable)
        else:
            desglose[variable] = _puntaje(variable, valor)

    puntos = sum(desglose.values())
    extremos = [n for n, p in desglose.items() if p == 3]
    niveles = _N2["nivel"]

    if puntos >= niveles["rojo_desde_total"]:
        nivel = "rojo"
    elif extremos:
        nivel = "rojo" if MODO_PARAMETRO_EXTREMO == "conservador" else "amarillo"
    elif puntos >= niveles["amarillo_desde_total"]:
        nivel = "amarillo"
    else:
        nivel = "verde"
    return ResultadoNews2(puntos, nivel, desglose, extremos, faltantes)


def captura_recomendada_min(nivel: str) -> float:
    """Minutos recomendados hasta la próxima captura, según el nivel actual."""
    return UMBRALES["captura_recomendada_min"][nivel]


def evaluar_o2_cabina(o2_pct: float) -> str:
    """Evalúa la concentración de O2 en cabina (%). Avisa tanto por hipoxia ambiental (bajo) como por riesgo de incendio/hiperoxia (alto)."""
    o = _AMB["o2_pct"]
    if o2_pct < o["rojo_bajo"] or o2_pct > o["rojo_alto"]:
        return "rojo"
    if o2_pct < o["amarillo_bajo"] or o2_pct > o["amarillo_alto"]:
        return "amarillo"
    return "verde"


def evaluar_ambiente(co2_mmhg: float | None = None, dosis_pct: float | None = None,
                     o2_pct: float | None = None) -> str:
    """Peor nivel entre CO2, O2 de cabina y dosis acumulada (% del límite de misión)."""
    niveles = ["verde"]
    if co2_mmhg is not None:
        c = _AMB["co2_mmhg"]
        niveles.append("rojo" if co2_mmhg > c["rojo_sobre"]
                       else "amarillo" if co2_mmhg > c["amarillo_sobre"] else "verde")
    if o2_pct is not None:
        niveles.append(evaluar_o2_cabina(o2_pct))
    if dosis_pct is not None:
        d = _AMB["dosis_pct"]
        niveles.append("rojo" if dosis_pct >= d["rojo_desde"]
                       else "amarillo" if dosis_pct >= d["amarillo_desde"] else "verde")
    return max(niveles, key=_ORDEN.__getitem__)


def evaluar_glucosa(mg_dl: float) -> tuple[str, bool]:
    """Devuelve (nivel, observacion). Supuesto: umbrales pendientes de validación médica."""
    g = _GLU
    if mg_dl < g["rojo_menor_que"] or mg_dl >= g["rojo_desde"]:
        return "rojo", False
    if mg_dl < g["amarillo_menor_que"] or mg_dl >= g["amarillo_desde"]:
        return "amarillo", False
    return "verde", g["observacion_desde"] <= mg_dl <= g["observacion_hasta"]


def evaluar_sueno(horas: float) -> tuple[str, bool]:
    """Supuesto de diseño: pocas horas dormidas son un aviso (amarillo), nunca rojo por sí solas."""
    return ("amarillo" if horas < UMBRALES["sueno_horas"]["amarillo_menor_que"] else "verde"), False


def animo_bajo(valor: int) -> bool:
    """Autorreporte 1 a 5. Supuesto: valores bajos activan apoyo privado, no alertas."""
    return valor <= UMBRALES["animo"]["bajo_menor_igual"]


def evaluar_diastolica(mmhg: float) -> tuple[str, bool]:
    """Supuesto: valores bajos se marcan como observación de perfusión, no como alerta."""
    return "verde", mmhg < UMBRALES["diastolica_mmhg"]["observacion_menor_que"]


def piso_de(indicador: str) -> float:
    """Variación mínima apreciable para ese indicador (0 si no hay piso declarado)."""
    return float(_LB.get("piso_desviacion", {}).get(indicador, 0.0))


def desviacion_linea_base(valor: float, historial: Sequence[float], solo_baja: bool = False, piso: float = 0.0, solo_alta: bool = False) -> dict:
    """Compara `valor` con media y DE muestral del historial.

    Con `solo_baja` solo avisa cuando el valor queda POR DEBAJO de lo habitual (sueño, ejercicio, ánimo).
    Con `piso` la desviación efectiva nunca es menor que esa variación mínima: una serie muy estable no convierte
    una diferencia insignificante en un aviso."""
    n = len(historial)
    if n < MIN_MUESTRAS_BASE:
        return {
            "aplica": False,
            "estado": "insuficiente",
            "razon": f"se requieren al menos {MIN_MUESTRAS_BASE} muestras",
            "n": n,
            "aviso": False,
        }
    mu = statistics.fmean(historial)
    sigma = statistics.stdev(historial)
    efectiva = max(sigma, piso)
    if efectiva == 0:
        aviso = valor != mu
        z = None
    else:
        z = (valor - mu) / efectiva
        aviso = abs(z) > K_DESVIACIONES
    if solo_baja and valor >= mu:
        aviso = False
    if solo_alta and valor <= mu:               # menos tiempo despierto que lo habitual no es un problema
        aviso = False
    direccion = "baja" if solo_baja else "alta" if solo_alta else "dos_lados"
    return {
        "aplica": True,
        "estado": "aviso" if aviso else "normal",
        "razon": "fuera del límite configurado" if aviso else "dentro del límite configurado",
        "direccion": direccion,
        "n": n,
        "media": mu,
        "desviacion": sigma,
        "desviacion_efectiva": efectiva,
        "z": z,
        "limite_z": K_DESVIACIONES,
        "aviso": aviso,
    }
