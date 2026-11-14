"""Modelo del enlace con Tierra: perfiles de retardo y variación (jitter). Lógica pura y determinista."""
from __future__ import annotations

import json
import os
import random
from pathlib import Path

RUTA = Path(__file__).resolve().parents[1] / "datos" / "enlace.json"


class EnlaceInvalido(ValueError):
    pass


def cargar(ruta: Path | None = None) -> dict:
    datos = json.loads((ruta or RUTA).read_text(encoding="utf-8"))
    perfiles = datos.get("perfiles", {})
    if not perfiles:
        raise EnlaceInvalido("enlace.json sin perfiles")
    for clave, p in perfiles.items():
        if not isinstance(p.get("retardo_s"), (int, float)) or p["retardo_s"] <= 0:
            raise EnlaceInvalido(f"perfil '{clave}': retardo_s debe ser > 0")
    # Compatibilidad: variables de entorno antiguas sobrescriben los perfiles base.
    for clave, var in (("marte", "ORBIT_LATENCIA_MARTE_S"), ("luna", "ORBIT_LATENCIA_LUNA_S")):
        if os.getenv(var) and clave in perfiles:
            perfiles[clave]["retardo_s"] = float(os.environ[var])
    return datos


DATOS = cargar()
PERFILES = DATOS["perfiles"]


def entornos() -> tuple[str, ...]:
    return tuple(PERFILES)


def retardo_base_s(entorno: str) -> float:
    try:
        return float(PERFILES[entorno.lower()]["retardo_s"])
    except KeyError as e:
        raise KeyError(f"entorno desconocido: {entorno}") from e


def con_jitter(base_s: float, jitter_pct: float, rng: random.Random | None = None) -> float:
    """Varía `base_s` en ±jitter_pct %. Con jitter 0 devuelve exactamente la base."""
    if jitter_pct <= 0:
        return base_s
    u = (rng or random).uniform(-jitter_pct, jitter_pct) / 100.0
    return base_s * (1.0 + u)
