"""Carga y valida datos/umbrales.json (fuente única de umbrales clínicos).

Se puede apuntar a otro archivo con ORBIT_UMBRALES (por ejemplo, el aprobado por un clínico).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

RUTA_POR_DEFECTO = Path(__file__).resolve().parents[1] / "datos" / "umbrales.json"
NEWS2_VARIABLES = ("frecuencia_respiratoria", "spo2", "presion_sistolica",
                   "frecuencia_cardiaca", "temperatura")


class UmbralesInvalidos(ValueError):
    pass


def _validar_bandas(nombre: str, bandas: list) -> None:
    if not bandas or "hasta" in bandas[-1]:
        raise UmbralesInvalidos(f"{nombre}: la última banda no debe tener 'hasta'")
    previo = None
    for b in bandas[:-1]:
        if "hasta" not in b or "puntos" not in b:
            raise UmbralesInvalidos(f"{nombre}: cada banda necesita 'hasta' y 'puntos'")
        if previo is not None and b["hasta"] <= previo:
            raise UmbralesInvalidos(f"{nombre}: los 'hasta' deben ser estrictamente crecientes")
        previo = b["hasta"]
    for b in bandas:
        if b["puntos"] not in (0, 1, 2, 3):
            raise UmbralesInvalidos(f"{nombre}: 'puntos' debe estar entre 0 y 3")


def validar(datos: dict) -> dict:
    for clave in ("version", "estado", "perfil", "semaforo", "ventana_news2_min", "news2", "ambiente",
                  "glucosa_mg_dl", "diastolica_mmhg", "sueno_horas", "animo", "linea_base", "indicadores", "reglas_combinadas"):
        if clave not in datos:
            raise UmbralesInvalidos(f"Falta la sección '{clave}'")
    perfil = datos["perfil"]
    if not isinstance(perfil, dict) or not perfil.get("id") or not perfil.get("poblacion") \
            or perfil.get("tipo") not in ("experimental", "validado"):
        raise UmbralesInvalidos("perfil requiere id, poblacion y tipo experimental/validado")
    semaforo = datos["semaforo"]
    if not isinstance(semaforo, dict) or semaforo.get("niveles") != ["verde", "amarillo", "rojo"]:
        raise UmbralesInvalidos("semaforo.niveles debe ser ['verde', 'amarillo', 'rojo']")
    bandas = datos["news2"].get("bandas", {})
    for variable in NEWS2_VARIABLES:
        if variable not in bandas:
            raise UmbralesInvalidos(f"Faltan bandas NEWS2 para '{variable}'")
        _validar_bandas(variable, bandas[variable])
    cap = datos.get("captura_recomendada_min", {})
    if set(cap) != {"verde", "amarillo", "rojo"} or any(not isinstance(v, (int, float)) or v <= 0 for v in cap.values()):
        raise UmbralesInvalidos("captura_recomendada_min necesita verde, amarillo y rojo con minutos > 0")
    if not (cap["rojo"] <= cap["amarillo"] <= cap["verde"]):
        raise UmbralesInvalidos("captura_recomendada_min debe acortarse al subir la gravedad")
    if datos["news2"].get("modo_parametro_extremo") not in ("conservador", "rcp"):
        raise UmbralesInvalidos("modo_parametro_extremo debe ser 'conservador' o 'rcp'")
    for clave, d in datos["indicadores"].items():
        if d["min"] >= d["max"]:
            raise UmbralesInvalidos(f"indicador '{clave}': min debe ser menor que max")
    o2 = datos["ambiente"].get("o2_pct")
    if o2 is not None:
        req = ("rojo_bajo", "amarillo_bajo", "amarillo_alto", "rojo_alto")
        if any(k not in o2 or not isinstance(o2[k], (int, float)) for k in req) or not (
            o2["rojo_bajo"] < o2["amarillo_bajo"] < o2["amarillo_alto"] < o2["rojo_alto"]
        ):
            raise UmbralesInvalidos("o2_pct requiere rojo_bajo < amarillo_bajo < amarillo_alto < rojo_alto")
    pisos = datos["linea_base"].get("piso_desviacion", {})
    linea_base = datos["linea_base"]
    if linea_base.get("metodo") != "media_desviacion_muestral":
        raise UmbralesInvalidos("linea_base.metodo no reconocido")
    if not isinstance(linea_base.get("dias"), (int, float)) or linea_base["dias"] <= 0:
        raise UmbralesInvalidos("linea_base.dias debe ser > 0")
    if not isinstance(linea_base.get("min_muestras"), int) or linea_base["min_muestras"] < 2:
        raise UmbralesInvalidos("linea_base.min_muestras debe ser un entero >= 2")
    if not isinstance(linea_base.get("desviaciones"), (int, float)) or linea_base["desviaciones"] <= 0:
        raise UmbralesInvalidos("linea_base.desviaciones debe ser > 0")
    if any(not isinstance(v, (int, float)) or v <= 0 for v in pisos.values()):
        raise UmbralesInvalidos("linea_base.piso_desviacion: todos los valores deben ser números > 0")
    _validar_combinadas(datos)
    return datos


_OPS = (">", ">=", "<", "<=")
_NIVELES = ("verde", "amarillo", "rojo")


def _validar_combinadas(datos: dict) -> None:
    rc = datos["reglas_combinadas"]
    for r in rc.get("individuales", []):
        if r.get("nivel") not in _NIVELES or not r.get("condiciones"):
            raise UmbralesInvalidos(f"regla combinada '{r.get('id')}': nivel o condiciones inválidos")
        for c in r["condiciones"]:
            if c.get("indicador") not in datos["indicadores"] or c.get("op") not in _OPS \
                    or not isinstance(c.get("valor"), (int, float)):
                raise UmbralesInvalidos(f"regla combinada '{r['id']}': condición inválida {c}")
    col = rc.get("colectiva_co2")
    if col is not None and (col.get("nivel") not in _NIVELES or col.get("nivel_minimo") not in _NIVELES
                            or col.get("min_tripulantes", 0) < 1):
        raise UmbralesInvalidos("colectiva_co2: nivel, nivel_minimo o min_tripulantes inválidos")


def cargar(ruta: str | Path | None = None) -> dict:
    ruta = Path(ruta or os.getenv("ORBIT_UMBRALES") or RUTA_POR_DEFECTO)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise UmbralesInvalidos(f"No se pudo leer {ruta}: {e}") from e
    return validar(datos)


UMBRALES = cargar()
