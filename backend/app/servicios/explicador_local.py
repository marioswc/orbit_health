"""Explicaciones consultivas sin intervención en el motor clínico.

El modelo, si existe, solo recibe un resumen de un estado ya calculado. Nunca
decide el nivel, la prioridad ni las acciones procedimentales.
"""
from __future__ import annotations

import json
import logging
from ipaddress import ip_address
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .. import config
from ..dominio import guardia_ia

log = logging.getLogger("orbit.ia")
_LOOPBACKS = {"localhost", "127.0.0.1", "::1"}
AVISO_IA = "Texto generado por un modelo local. No es un diagnóstico y no modifica la alerta."


class _SinRedireccion(HTTPRedirectHandler):
    """Una dirección local no puede mandarnos a otra: solo se habla con el modelo configurado."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_ABRIDOR = build_opener(_SinRedireccion)


def _url_local(url: str) -> bool:
    try:
        host = urlparse(url).hostname
        if not host:
            return False
        if host in _LOOPBACKS:
            return True
        return ip_address(host).is_loopback
    except ValueError:
        return False


def _fallback(estado: dict) -> str:
    nivel = estado.get("nivel_general", "verde")
    news2 = estado.get("news2", {})
    faltantes = news2.get("faltantes") or []
    reglas = estado.get("reglas_combinadas") or []
    if nivel == "rojo":
        inicio = "El estado general es rojo porque el motor determinista detectó una señal de alta prioridad."
    elif nivel == "amarillo":
        inicio = "El estado general es amarillo porque el motor determinista detectó una señal que requiere seguimiento."
    else:
        inicio = "El estado general es verde según las lecturas vigentes y las reglas configuradas."
    partes = [inicio]
    if news2.get("puntos"):
        partes.append(f"La puntuación NEWS2 disponible es {news2['puntos']}.")
    if reglas:
        partes.append("También está activa: " + ", ".join(r["nombre"] for r in reglas) + ".")
    if faltantes:
        partes.append("La evaluación NEWS2 está incompleta; faltan: " + ", ".join(faltantes) + ".")
    partes.append("Esta explicación no es un diagnóstico ni modifica la alerta; sigue las acciones procedimentales mostradas.")
    return " ".join(partes)


def _prompt(estado: dict) -> str:
    resumen = {
        "nivel_general": estado.get("nivel_general"),
        "nivel_fisiologico": estado.get("nivel_fisiologico"),
        "news2": estado.get("news2"),
        "indicadores": estado.get("indicadores", []),
        "reglas_combinadas": estado.get("reglas_combinadas", []),
        "peligros_relacionados": estado.get("peligros_relacionados", []),
    }
    return (
        "Explica en español, en máximo 120 palabras, este resultado de un sistema de "
        "apoyo a la decisión para una tripulación espacial. Describe qué señales "
        "contribuyeron al nivel ya calculado y qué información falta. No diagnostiques, "
        "no prescribas tratamientos o medicamentos, no inventes valores y no cambies "
        "nivel, prioridad ni acciones. Indica que las acciones procedimentales del "
        "sistema tienen prioridad. Devuelve solo texto claro para el tripulante.\n\n"
        + json.dumps(resumen, ensure_ascii=False, sort_keys=True)
    )


def explicar(estado: dict) -> dict:
    """Genera una explicación local y devuelve siempre el nivel calculado intacto."""
    nivel = estado.get("nivel_general", "verde")
    url = config.IA_LOCAL_URL
    modelo = config.IA_LOCAL_MODELO
    if not url or not modelo or not _url_local(url):
        return {"fuente": "reglas_locales", "modelo": None, "generado_por_ia": False,
                "explicacion": _fallback(estado), "nivel_general": nivel}

    texto = consultar_modelo(_prompt(estado))
    if texto is None:
        return {"fuente": "reglas_locales", "modelo": None, "generado_por_ia": False,
                "explicacion": _fallback(estado), "nivel_general": nivel}
    ok, motivo = guardia_ia.validar_respuesta(texto, estado)
    if not ok:                                              # lo que el modelo dijo no pasa: se usa el texto determinista
        log.warning("Respuesta del modelo local descartada: %s", motivo)
        return {"fuente": "reglas_locales", "modelo": None, "generado_por_ia": False, "descartado_por": motivo,
                "explicacion": _fallback(estado), "nivel_general": nivel}
    return {"fuente": "modelo_local", "modelo": modelo, "generado_por_ia": True, "aviso": AVISO_IA,
            "explicacion": texto, "nivel_general": nivel}


def consultar_modelo(prompt: str) -> str | None:
    """Consulta el modelo configurado y devuelve None si no está disponible."""
    url = config.IA_LOCAL_URL
    modelo = config.IA_LOCAL_MODELO
    if not url or not modelo or not _url_local(url):
        return None
    payload = json.dumps({
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1},
    }).encode("utf-8")
    request = Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with _ABRIDOR.open(request, timeout=max(0.5, config.IA_LOCAL_TIMEOUT_S)) as response:
            body = json.loads(response.read().decode("utf-8"))
        texto = body.get("response")
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError("el modelo local no devolvió texto")
        return texto.strip()[:2000]
    except (URLError, TimeoutError, OSError, ValueError, UnicodeDecodeError) as error:
        log.warning("No se pudo consultar el modelo local; se usa fallback: %s", error)
        return None
