"""Integración con el marco de peligros y riesgos del Programa de Investigación Humana (HRP) de la NASA.

Los 5 peligros y los 17 riesgos son los de las páginas oficiales. La asociación de cada indicador con un peligro
es una decisión de diseño del equipo, no una clasificación oficial, y el archivo lo declara.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .catalogos import INDICADORES

RUTA = Path(__file__).resolve().parents[1] / "datos" / "peligros.json"
COBERTURAS = ("cubierto", "parcial", "no_cubierto")


class PeligrosInvalidos(ValueError):
    pass


def cargar(ruta: Path | None = None) -> dict:
    d = json.loads((ruta or RUTA).read_text(encoding="utf-8"))
    for clave, ps in d["indicadores_por_peligro"].items():
        for p in ps:
            if p not in d["peligros"]:
                raise PeligrosInvalidos(f"indicador '{clave}' apunta a un peligro inexistente: {p}")
    for r in d["riesgos"]:
        if r["cobertura"] not in COBERTURAS:
            raise PeligrosInvalidos(f"riesgo '{r['nombre_oficial']}': cobertura inválida")
        if not r["url"].startswith("https://www.nasa.gov/"):
            raise PeligrosInvalidos(f"riesgo '{r['nombre_oficial']}': URL no oficial")
        if r["cobertura"] != "no_cubierto" and not r["indicadores"]:
            raise PeligrosInvalidos(f"riesgo '{r['nombre_oficial']}': dice estar cubierto pero no declara indicadores")
    return d


DATOS = cargar()


def peligros_de(indicadores: Iterable[str]) -> list[dict]:
    """Peligros relacionados con una lista de indicadores (sin repetir, en orden de aparición)."""
    vistos: dict[str, dict] = {}
    for ind in indicadores:
        for p in DATOS["indicadores_por_peligro"].get(ind, []):
            vistos.setdefault(p, {"id": p, "nombre": DATOS["peligros"][p]["nombre"], "url": DATOS["peligros"][p]["url"]})
    return list(vistos.values())


def resumen_cobertura() -> dict:
    cuenta = {c: 0 for c in COBERTURAS}
    for r in DATOS["riesgos"]:
        cuenta[r["cobertura"]] += 1
    return {"total": len(DATOS["riesgos"]), **cuenta}


def indicadores_conocidos() -> set[str]:
    return set(INDICADORES) | {"animo"}
