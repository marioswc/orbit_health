"""Dispositivo portátil simulado: genera indicadores plausibles, repetibles con una semilla.

Incluye ruido temporalmente autocorrelacionado (proceso amortiguado tipo Ornstein-Uhlenbeck),
acoplamiento fisiológico cardiorrespiratorio/hemodinámico, cobertura de todas las reglas clínicas
del motor y opción de inyectar artefactos de movimiento puntuales para verificar el filtro de mediana.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random
import statistics

BASE = {
    "frecuencia_respiratoria": 16,
    "spo2": 97,
    "presion_sistolica": 120,
    "presion_diastolica": 78,
    "frecuencia_cardiaca": 70,
    "temperatura": 36.7,
    "avpu": 0,
    "variabilidad_cardiaca": 48,
}
# Ruido máximo (±) por señal: acotado, para que un perfil estable no salga de su rango normal.
RUIDO = {
    "frecuencia_respiratoria": 1,
    "spo2": 1,
    "presion_sistolica": 3,
    "presion_diastolica": 2,
    "frecuencia_cardiaca": 2,
    "temperatura": 0.1,
    "avpu": 0,
    "variabilidad_cardiaca": 3,
}
INERCIA_RUIDO = 0.55  # persistencia temporal entre ticks consecutivos (0 = ruido blanco, <1 = caminata amortiguada)

# Cambio total a lo largo de la serie para las constantes base.
DERIVA = {
    "estable": {},
    "deterioro_respiratorio": {
        "spo2": -9,
        "frecuencia_respiratoria": 11,
        "frecuencia_cardiaca": 48,
        "presion_sistolica": -10,
        "presion_diastolica": -6,
        "temperatura": 0.3,
        "variabilidad_cardiaca": -24,
    },
    "proceso_infeccioso": {
        "temperatura": 1.9,
        "frecuencia_cardiaca": 28,
        "frecuencia_respiratoria": 5,
        "presion_sistolica": -6,
        "presion_diastolica": -4,
        "variabilidad_cardiaca": -18,
    },
    "intolerancia_ortostatica": {
        "frecuencia_cardiaca": 30,
        "presion_sistolica": -22,
        "presion_diastolica": -22,
        "variabilidad_cardiaca": -22,
    },
    "hipoglucemia": {
        "frecuencia_cardiaca": 25,
        "frecuencia_respiratoria": 3,
        "variabilidad_cardiaca": -20,
    },
    "hipoxia_ambiental_o2": {
        "spo2": -6,
        "frecuencia_respiratoria": 7,
        "frecuencia_cardiaca": 24,
        "variabilidad_cardiaca": -16,
    },
}
DOSIS_RADIACION = {
    "exposicion_radiacion": (68.0, 95.0),
}
# Indicadores específicos de ciertos perfiles: (inicio, fin, ruido_max, decimales)
SERIES_ESPECIALES = {
    "hipoglucemia": {"glucosa": (94.0, 48.0, 1.5, 0)},
    "hipoxia_ambiental_o2": {"o2_cabina": (20.9, 18.6, 0.05, 2)},
}
PERFILES = tuple(dict.fromkeys((*DERIVA, *DOSIS_RADIACION, *SERIES_ESPECIALES)))

# Artefacto de movimiento no extremo (2 puntos NEWS2): altera un promedio simple pero la mediana lo filtra.
ARTEFACTO_VALORES = {
    "frecuencia_cardiaca": 124.0,
    "frecuencia_respiratoria": 23.0,
}


def _acotar(valor: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(maximo, valor))


def generar(perfil: str, ticks: int, semilla: int | None = None,
            artefactos: bool = False) -> list[dict[str, float]]:
    """Una lectura de cada signo por 'tick'. Con la misma semilla produce siempre la misma serie."""
    if perfil not in PERFILES:
        raise ValueError(f"perfil debe ser uno de: {', '.join(PERFILES)}")
    if not 1 <= ticks <= 60:
        raise ValueError("ticks debe estar entre 1 y 60")
    rng = random.Random(semilla)
    estado_ruido = {signo: 0.0 for signo in BASE}
    tick_artefacto = ticks // 2 if artefactos and ticks >= 3 else -1
    serie = []
    for i in range(ticks):
        avance = i / (ticks - 1) if ticks > 1 else 0.0
        for signo in BASE:
            amplitud = RUIDO[signo]
            innovacion = rng.uniform(-amplitud, amplitud) if amplitud > 0 else 0.0
            estado_ruido[signo] = INERCIA_RUIDO * estado_ruido[signo] + (1.0 - INERCIA_RUIDO) * innovacion

        # Acoplamiento fisiológico acotado dentro de la banda de ruido de cada señal:
        # 1) Arritmia sinusal respiratoria (FR -> FC)
        # 2) Coherencia hemodinámica sistólica-diastólica (PAS -> PAD)
        # 3) Retirada vagal (FC -> RMSSD inverso)
        ruido_fr = estado_ruido["frecuencia_respiratoria"]
        ruido_ps = estado_ruido["presion_sistolica"]
        ruido_fc = _acotar(0.80 * estado_ruido["frecuencia_cardiaca"] + 0.40 * ruido_fr,
                           -RUIDO["frecuencia_cardiaca"], RUIDO["frecuencia_cardiaca"])
        ruido_pd = _acotar(0.65 * estado_ruido["presion_diastolica"] + 0.25 * ruido_ps,
                           -RUIDO["presion_diastolica"], RUIDO["presion_diastolica"])
        ruido_hrv = _acotar(0.75 * estado_ruido["variabilidad_cardiaca"] - 0.35 * ruido_fc,
                            -RUIDO["variabilidad_cardiaca"], RUIDO["variabilidad_cardiaca"])
        ruidos_acoplados = {
            **estado_ruido,
            "frecuencia_cardiaca": ruido_fc,
            "presion_diastolica": ruido_pd,
            "variabilidad_cardiaca": ruido_hrv,
        }

        tick: dict[str, float] = {}
        deriva_perfil = DERIVA.get(perfil, {})
        for signo, base in BASE.items():
            valor = base + deriva_perfil.get(signo, 0) * avance + ruidos_acoplados[signo]
            tick[signo] = round(valor, 1) if signo == "temperatura" else float(round(valor))

        if perfil in DOSIS_RADIACION:
            inicio, fin = DOSIS_RADIACION[perfil]
            tick["dosis_pct"] = round(inicio + (fin - inicio) * avance, 1)

        if perfil in SERIES_ESPECIALES:
            for ind, (inicio, fin, amp, dec) in SERIES_ESPECIALES[perfil].items():
                ruido_esp = rng.uniform(-amp, amp) if amp > 0 else 0.0
                val_esp = inicio + (fin - inicio) * avance + ruido_esp
                tick[ind] = round(val_esp, dec) if dec > 0 else float(round(val_esp))

        if i == tick_artefacto:
            tick.update(ARTEFACTO_VALORES)

        serie.append(tick)
    return serie


def simular_ventana_con_artefacto(conn, tid: str = "T1", muestras: int = 7, semilla: int = 7) -> dict:
    """Envía una serie estable con un artefacto de movimiento al flujo continuo y demuestra el filtro de mediana."""
    from ..servicios import flujo
    if muestras < 3:
        raise ValueError("muestras debe ser al menos 3")
    serie = generar("estable", muestras, semilla=semilla, artefactos=True)
    t0 = datetime.now(timezone.utc)
    crudos_fc = [t["frecuencia_cardiaca"] for t in serie]
    for idx, tick in enumerate(serie):
        flujo.ingresar(conn, tid, "frecuencia_cardiaca", tick["frecuencia_cardiaca"],
                       ahora=t0 + timedelta(seconds=idx * 5), origen="simulado")
    cierre = flujo.vaciar(conn, tid)
    res_fc = next(r for r in cierre["resultados"] if r["indicador"] == "frecuencia_cardiaca")
    valor_mediana = res_fc["lectura"]["valor"] if "valor" in res_fc["lectura"] else statistics.median(crudos_fc)
    return {
        "muestras_crudas_fc": crudos_fc,
        "pico_artefacto_fc": max(crudos_fc),
        "promedio_sin_filtro": round(statistics.fmean(crudos_fc), 1),
        "mediana_registrada": float(valor_mediana),
        "nivel_registrado": res_fc["lectura"]["nivel"],
    }
