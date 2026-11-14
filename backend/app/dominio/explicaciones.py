"""Contenido educativo por indicador: qué es, por qué se mide, cómo medirlo y qué cambia en el espacio.

Son explicaciones generales, sin indicaciones de tratamiento ni medicación. Pendiente de validación clínica.
"""
import json
from pathlib import Path

RUTA = Path(__file__).resolve().parents[1] / "datos" / "explicaciones.json"
CAMPOS = ("que_es", "por_que_se_mide", "como_medirlo", "en_el_espacio", "cuando_avisar", "fuentes")


class ExplicacionesInvalidas(ValueError):
    pass


def cargar(ruta: Path | None = None) -> dict:
    datos = json.loads((ruta or RUTA).read_text(encoding="utf-8"))
    for clave, e in datos["explicaciones"].items():
        faltan = [c for c in CAMPOS if not e.get(c)]
        if faltan:
            raise ExplicacionesInvalidas(f"explicación '{clave}' sin: {', '.join(faltan)}")
        if not all(str(u).startswith("https://") for u in e["fuentes"]):
            raise ExplicacionesInvalidas(f"explicación '{clave}': las fuentes deben ser https")
        for campo in ("medidas_nasa", "senales_a_vigilar"):
            for item in e.get(campo, []):
                if not (item.get("texto") and item.get("cita") and str(item.get("fuente", "")).startswith("https://www.nasa.gov/")):
                    raise ExplicacionesInvalidas(f"explicación '{clave}': cada elemento de {campo} necesita texto, cita textual y fuente de nasa.gov")
        if e.get("habitos_generales") and not e.get("habitos_generales_origen"):
            raise ExplicacionesInvalidas(f"explicación '{clave}': los hábitos generales deben declarar que no son de la NASA")
    return datos


DATOS = cargar()
