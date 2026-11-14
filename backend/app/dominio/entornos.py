"""Entornos de la misión (nave, estación, base lunar o marciana, rover) y qué cambia en la salud con la gravedad.

Sirve sobre todo para no aplicar a un entorno una cifra que solo vale para otro: la pérdida ósea de 1 a 1.5 % por mes
es de microgravedad, no de gravedad parcial.
"""
import json
from pathlib import Path

RUTA = Path(__file__).resolve().parents[1] / "datos" / "entornos.json"
ESTADOS_OSEA = ("aplica", "no_caracterizada")


class EntornosInvalidos(ValueError):
    pass


def cargar(ruta: Path | None = None) -> dict:
    d = json.loads((ruta or RUTA).read_text(encoding="utf-8"))
    for clave, x in d["entornos"].items():
        g = x["gravedad_g"]
        if g is not None and (not isinstance(g, (int, float)) or g < 0):
            raise EntornosInvalidos(f"'{clave}': la gravedad debe ser un número >= 0 o null")
        if x["microgravedad"] and g != 0:
            raise EntornosInvalidos(f"'{clave}': microgravedad implica gravedad 0")
        e = x["estimacion_osea"]
        if e["estado"] not in ESTADOS_OSEA or not e["nota"]:
            raise EntornosInvalidos(f"'{clave}': estimación ósea inválida")
        if e["estado"] == "aplica" and not x["microgravedad"]:
            raise EntornosInvalidos(f"'{clave}': la cifra ósea solo puede aplicar en microgravedad")
    return d


DATOS = cargar()
