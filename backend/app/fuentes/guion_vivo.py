"""Guion de una misión en vivo: qué valores "mide" cada banda en cada instante, y qué le pasa al enlace.

Es lógica pura y determinista (misma semilla, mismos valores), por eso se puede probar sin esperar. Los valores son
hipotéticos y sirven solo para la demostración.

Los tiempos van en minutos de MISIÓN simulada, no de reloj: el motor decide cuántos minutos avanza cada segundo real.
"""
from __future__ import annotations

import random

from .dispositivo_simulado import BASE, RUIDO

TRIPULANTES = ("T1", "T2", "T3", "T4")
# Cada tripulante tiene su propia línea base (nadie tiene el mismo pulso en reposo).
BASE_PERSONAL = {
    "T1": {**BASE, "frecuencia_cardiaca": 70},
    "T2": {**BASE, "frecuencia_cardiaca": 66, "spo2": 98},
    "T3": {**BASE, "frecuencia_cardiaca": 74},
    "T4": {**BASE, "frecuencia_cardiaca": 68, "presion_sistolica": 116},
}

# (minuto, valor): se interpola en línea recta entre puntos y se mantiene el último valor.
CURVAS = {
    "T1": {  # el comandante sufre un deterioro respiratorio y se recupera
        "spo2": [(0, 97), (8, 97), (20, 88), (26, 93), (32, 97)],
        "frecuencia_respiratoria": [(0, 16), (8, 16), (20, 27), (26, 20), (32, 16)],
        "frecuencia_cardiaca": [(0, 70), (8, 70), (20, 122), (26, 95), (32, 72)],
        "presion_sistolica": [(0, 120), (8, 120), (20, 106), (32, 120)],
        "temperatura": [(0, 36.7), (14, 36.7), (22, 37.4), (32, 36.8)],
    },
    "T2": {  # T2 se ve afectado más tarde y de forma más leve (sin ningún signo extremo por sí solo)
        "spo2": [(0, 98), (10, 98), (18, 93), (30, 98)],   # mínimo 93: con el ruido (±1) nunca baja a 91, que sería extremo
        "frecuencia_respiratoria": [(0, 16), (10, 16), (18, 23), (30, 16)],
        "frecuencia_cardiaca": [(0, 66), (10, 66), (18, 112), (30, 68)],
    },
}
# El CO₂ de la cabina lo registra T3 (el sensor de la cabina se asigna a un tripulante).
CURVA_CO2 = [(0, 2.6), (6, 2.6), (18, 3.9), (26, 3.1), (32, 2.7)]
SIGNOS = ("frecuencia_respiratoria", "spo2", "presion_sistolica", "frecuencia_cardiaca", "temperatura")

DURACION_MIN = 34.0
ENTORNO_INICIAL = "marte_cercano"
# (minuto, enlace activo?, texto)
EVENTOS_ENLACE = [(0.0, True, "Enlace activo con la Tierra"),
                  (14.0, False, "Conjunción solar: se pierde el enlace y los eventos quedan retenidos a bordo"),
                  (22.0, True, "Vuelve el enlace: sale primero lo más urgente")]
# Marcas de la historia para narrar la demo (no cambian ningún dato).
NARRACION = [(0.0, "Inicio: tripulación estable y bandas conectadas"),
             (6.0, "El CO₂ de la cabina empieza a subir"),
             (8.0, "T1 empieza a respirar más rápido"),
             (11.0, "La línea base personal de T1 detecta el cambio antes que las reglas estándar"),
             (12.5, "T2 también se ve afectado y el CO₂ ya está alto: salta la alerta colectiva"),
             (14.0, "Conjunción solar: se pierde el enlace; los eventos quedan retenidos a bordo"),
             (16.0, "T1 pasa a rojo con el enlace caído: la tripulación lo ve al instante y su alerta espera a bordo"),
             (22.0, "Vuelve el enlace: sale primero lo urgente"),
             (26.0, "Se corrige la depuración de CO₂ y la tripulación mejora"),
             (32.0, "Tripulación recuperada")]
# Una sola vez al empezar: resumen diario que entrega la banda (sueño) y, al final, el ejercicio.
SUENO_INICIAL = {"T1": 7.2, "T2": 6.6, "T3": 5.8, "T4": 7.8}
# Calidad del sueño que reporta un reloj de actigrafía (como en el estudio ARCHeR de NASA): valores inventados.
SUENO_EFICIENCIA_INICIAL = {"T1": 91, "T2": 89, "T3": 84, "T4": 93}
SUENO_DESPERTARES_INICIAL = {"T1": 25, "T2": 32, "T3": 50, "T4": 20}
EJERCICIO_FINAL = {"T1": 45, "T2": 60, "T3": 30, "T4": 50}


def interpolar(puntos: list[tuple[float, float]], minuto: float) -> float:
    if minuto <= puntos[0][0]:
        return puntos[0][1]
    for (t0, v0), (t1, v1) in zip(puntos, puntos[1:]):
        if minuto <= t1:
            return v0 + (v1 - v0) * (minuto - t0) / (t1 - t0)
    return puntos[-1][1]


def _innovacion(semilla: int, tid: str, signo: str, tick: int, amplitud: float) -> float:
    return random.Random(f"{semilla}|{tid}|{signo}|{max(0, tick)}").uniform(-amplitud, amplitud)


PESOS_TEMPORALES = (0.50, 0.35, 0.15)
# Artefacto puntual de movimiento (1 solo tick en T4): sube el pulso a 124 lpm (no extremo),
# para demostrar que la ventana de mediana del flujo continuo lo absorbe sin generar falsa alarma.
ARTEFACTOS_MOVIMIENTO: dict[tuple[str, str, int], float] = {
    ("T4", "frecuencia_cardiaca", 9): 124.0,
}


def _ruido(semilla: int, tid: str, signo: str, tick: int, amplitud: float) -> float:
    """Ruido temporalmente autocorrelacionado (filtro ponderado de 3 ticks) y acotado en [-amplitud, +amplitud]."""
    return sum(peso * _innovacion(semilla, tid, signo, tick - k, amplitud)
               for k, peso in enumerate(PESOS_TEMPORALES))


def valor_en(tid: str, signo: str, minuto: float, tick: int, semilla: int) -> float:
    """Valor que mide la banda de `tid` para `signo` en ese minuto de misión (con ruido acotado y repetible)."""
    if (tid, signo, tick) in ARTEFACTOS_MOVIMIENTO:
        return ARTEFACTOS_MOVIMIENTO[(tid, signo, tick)]
    puntos = CURVAS.get(tid, {}).get(signo)
    base = interpolar(puntos, minuto) if puntos else BASE_PERSONAL[tid][signo]
    ruido_propio = _ruido(semilla, tid, signo, tick, RUIDO[signo])
    if signo == "frecuencia_cardiaca":
        # Acoplamiento cardiorrespiratorio (arritmia sinusal respiratoria) acotado en [-RUIDO['frecuencia_cardiaca'], +RUIDO['frecuencia_cardiaca']]
        ruido_resp = _ruido(semilla, tid, "frecuencia_respiratoria", tick, RUIDO[signo])
        v = base + (0.80 * ruido_propio + 0.20 * ruido_resp)
    else:
        v = base + ruido_propio
    return round(v, 1) if signo == "temperatura" else float(round(v))


def co2_en(minuto: float, tick: int, semilla: int) -> float:
    return round(interpolar(CURVA_CO2, minuto) + _ruido(semilla, "cabina", "co2", tick, 0.05), 2)


def muestras_en(minuto: float, tick: int, semilla: int) -> list[tuple[str, str, float]]:
    """Todas las muestras de ese instante: (tripulante, indicador, valor)."""
    salida = [(tid, signo, valor_en(tid, signo, minuto, tick, semilla)) for tid in TRIPULANTES for signo in SIGNOS]
    salida.append(("T3", "co2", co2_en(minuto, tick, semilla)))
    return salida


def eventos_enlace_entre(desde_min: float, hasta_min: float) -> list[tuple[float, bool, str]]:
    """Cambios de enlace que ocurren en el tramo (desde, hasta]. El del minuto 0 se incluye con desde < 0."""
    return [e for e in EVENTOS_ENLACE if desde_min < e[0] <= hasta_min]
