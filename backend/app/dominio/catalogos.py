"""Catálogo de indicadores y rangos de captura. Los valores viven en datos/umbrales.json."""
from .umbrales import UMBRALES

# clave: (etiqueta, unidad, mínimo, máximo)
INDICADORES = {k: (d["etiqueta"], d["unidad"], d["min"], d["max"])
               for k, d in UMBRALES["indicadores"].items()}

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
