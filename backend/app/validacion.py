"""Catálogo de indicadores y rangos de captura (supuestos de diseño, validar con médico)."""

# clave: (etiqueta, unidad, mínimo, máximo)
INDICADORES = {
    "temperatura": ("Temperatura", "°C", 30.0, 43.0),
    "presion_sistolica": ("Presión sistólica", "mmHg", 40, 280),
    "presion_diastolica": ("Presión diastólica", "mmHg", 20, 180),
    "frecuencia_cardiaca": ("Frecuencia cardíaca", "lpm", 20, 250),
    "frecuencia_respiratoria": ("Frecuencia respiratoria", "rpm", 4, 60),
    "spo2": ("SpO₂", "%", 50, 100),
    "avpu": ("Conciencia (AVPU)", "AVPU", 0, 3),
    "glucosa": ("Glucosa capilar", "mg/dL", 20, 600),
    "co2": ("CO₂ de cabina", "mmHg", 0, 20),
    "dosis_pct": ("Dosis acumulada", "% del límite", 0, 200),
}

NEWS2_VARS = ("frecuencia_respiratoria", "spo2", "presion_sistolica",
              "frecuencia_cardiaca", "avpu", "temperatura")


def validar(indicador: str, valor: float) -> str | None:
    """Devuelve mensaje de error o None si es válido."""
    if indicador not in INDICADORES:
        return f"Indicador desconocido: {indicador}"
    _, _, lo, hi = INDICADORES[indicador]
    if not (lo <= valor <= hi):
        return f"{indicador} fuera de rango de captura ({lo}–{hi})"
    return None
