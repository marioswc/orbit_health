"""Explicaciones consultivas sin intervención en el motor clínico.

El modelo, si existe, solo recibe un resumen de un estado ya calculado. Nunca
decide el nivel, la prioridad ni las acciones procedimentales.
"""
from __future__ import annotations

import json
import logging
import ssl
from ipaddress import ip_address
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from .. import config
from ..dominio import guardia_ia
from ..dominio.acciones import DETALLES, ESTILO_POR_DEFECTO, TONOS

log = logging.getLogger("orbit.ia")
_LOOPBACKS = {"localhost", "127.0.0.1", "::1"}
AVISO_IA = "Texto generado por un modelo local. No es un diagnóstico y no modifica la alerta."
AVISO_IA_EXTERNA = ("Texto generado por IA en un servicio externo por internet (DeepSeek): tu consulta y tu estado salieron de la estación. "
                    "No es un diagnóstico y no modifica la alerta.")


def aviso_para(fuente: str) -> str:
    return AVISO_IA_EXTERNA if fuente == "deepseek" else AVISO_IA


class _SinRedireccion(HTTPRedirectHandler):
    """Una dirección local no puede mandarnos a otra: solo se habla con el modelo configurado."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _contexto_ssl() -> ssl.SSLContext:
    """Usa el bundle de certifi (o /etc/ssl/cert.pem en macOS) cuando Python no trae certificados del sistema."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        cafile = "/etc/ssl/cert.pem" if Path("/etc/ssl/cert.pem").is_file() else None
        return ssl.create_default_context(cafile=cafile)


_ABRIDOR = build_opener(_SinRedireccion, HTTPSHandler(context=_contexto_ssl()))


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


def _fallback(estado: dict, preferencias: dict | None = None) -> str:
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
    tono, detalle = _estilo(preferencias)
    if detalle == "breve":                      # lo esencial: el nivel y el aviso, sin el detalle intermedio
        partes = [partes[0], partes[-1]]
    if tono == "calido":
        partes.insert(0, "Vamos paso a paso.")
    return " ".join(partes)


def _estilo(preferencias: dict | None) -> tuple[str, str]:
    """(tono, detalle) válidos; cualquier otra cosa vuelve al valor por defecto. Solo se leen opciones elegidas de una lista."""
    p = preferencias or {}
    return (p["tono"] if p.get("tono") in TONOS else ESTILO_POR_DEFECTO["tono"],
            p["detalle"] if p.get("detalle") in DETALLES else ESTILO_POR_DEFECTO["detalle"])


def _prompt(estado: dict, preferencias: dict | None = None) -> str:
    tono, detalle = _estilo(preferencias)
    palabras = 60 if detalle == "breve" else 120
    voz = ("Habla con calidez y cercanía, sin dramatizar." if tono == "calido" else "Habla de forma directa y sobria.")
    resumen = {
        "nivel_general": estado.get("nivel_general"),
        "nivel_fisiologico": estado.get("nivel_fisiologico"),
        "news2": estado.get("news2"),
        "indicadores": estado.get("indicadores", []),
        "reglas_combinadas": estado.get("reglas_combinadas", []),
        "peligros_relacionados": estado.get("peligros_relacionados", []),
    }
    return (
        f"Explica en español, en máximo {palabras} palabras. {voz} Es el resultado de un sistema de "
        "apoyo a la decisión para una tripulación espacial. Describe qué señales "
        "contribuyeron al nivel ya calculado y qué información falta. No diagnostiques, "
        "no prescribas tratamientos o medicamentos, no inventes valores y no cambies "
        "nivel, prioridad ni acciones. Indica que las acciones procedimentales del "
        "sistema tienen prioridad. Devuelve solo texto claro para el tripulante.\n\n"
        + json.dumps(resumen, ensure_ascii=False, sort_keys=True)
    )


def _usar_deepseek() -> bool:
    return config.IA_PROVEEDOR != "local" and bool(config.DEEPSEEK_API_KEY)


def _modelo_activo() -> tuple[str, str] | None:
    """Devuelve (fuente, modelo) si hay un proveedor listo, o None si solo aplican reglas locales."""
    if _usar_deepseek():
        return "deepseek", config.DEEPSEEK_MODELO
    url, modelo = config.IA_LOCAL_URL, config.IA_LOCAL_MODELO
    if url and modelo and _url_local(url):
        return "modelo_local", modelo
    return None


def explicar(estado: dict, preferencias: dict | None = None) -> dict:
    """Genera una explicación con el proveedor configurado y devuelve siempre el nivel calculado intacto."""
    nivel = estado.get("nivel_general", "verde")
    activo = _modelo_activo()
    if not activo:
        return {"fuente": "reglas_locales", "modelo": None, "generado_por_ia": False,
                "explicacion": _fallback(estado, preferencias), "nivel_general": nivel}
    fuente, modelo = activo

    texto = consultar_modelo(_prompt(estado, preferencias))
    if texto is None:
        return {"fuente": "reglas_locales", "modelo": None, "generado_por_ia": False,
                "explicacion": _fallback(estado, preferencias), "nivel_general": nivel}
    ok, motivo = guardia_ia.validar_respuesta(texto, estado)
    if not ok:                                              # lo que el modelo dijo no pasa: se usa el texto determinista
        log.warning("Respuesta del modelo descartada: %s", motivo)
        return {"fuente": "reglas_locales", "modelo": None, "generado_por_ia": False, "descartado_por": motivo,
                "explicacion": _fallback(estado, preferencias), "nivel_general": nivel}
    return {"fuente": fuente, "modelo": modelo, "generado_por_ia": True, "aviso": aviso_para(fuente),
            "explicacion": texto, "nivel_general": nivel}


def _consultar_deepseek(prompt: str, system: str | None = None) -> str | None:
    cuerpo: dict = {
        "model": config.DEEPSEEK_MODELO,
        "messages": ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "stream": False,
    }
    if "flash" in config.DEEPSEEK_MODELO:
        cuerpo["thinking"] = {"type": "disabled"}
    payload = json.dumps(cuerpo).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
        "User-Agent": "ORBIT-Health/1.0",
    }
    request = Request(config.DEEPSEEK_URL, data=payload, headers=headers, method="POST")
    try:
        with _ABRIDOR.open(request, timeout=max(0.5, config.DEEPSEEK_TIMEOUT_S)) as response:
            body = json.loads(response.read().decode("utf-8"))
        texto = body["choices"][0]["message"]["content"]
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError("DeepSeek no devolvió texto")
        return texto.strip()[:2000]
    except (URLError, TimeoutError, OSError, ValueError, UnicodeDecodeError, KeyError, IndexError, TypeError) as error:
        log.warning("No se pudo consultar DeepSeek; se usa fallback: %s", error)
        return None


def consultar_modelo(prompt: str, system: str | None = None) -> str | None:
    """Consulta el proveedor configurado (DeepSeek o Ollama local) y devuelve None si no está disponible."""
    if _usar_deepseek():
        return _consultar_deepseek(prompt, system)
    url = config.IA_LOCAL_URL
    modelo = config.IA_LOCAL_MODELO
    if not url or not modelo or not _url_local(url):
        return None
    cuerpo = {
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "keep_alive": config.IA_LOCAL_KEEP_ALIVE,                 # el modelo se queda en memoria entre preguntas
        # num_predict: un modelo chico no debe quedarse generando; num_ctx: contexto corto = respuesta más rápida
        "options": {"temperature": 0.1, "num_predict": 220, "num_ctx": 2048},
    }
    if system:
        cuerpo["system"] = system          # las reglas van aparte de los datos: un modelo chico las respeta mejor
    payload = json.dumps(cuerpo).encode("utf-8")
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


def precalentar_modelo() -> bool:
    """Carga el modelo local en memoria con una petición mínima, para que la primera pregunta real no pague la carga.
    Nunca toca un proveedor externo ni lanza excepciones: si no hay modelo local, no hace nada."""
    url, modelo = config.IA_LOCAL_URL, config.IA_LOCAL_MODELO
    if _usar_deepseek() or not url or not modelo or not _url_local(url):
        return False
    from .voz_local import SISTEMA_BASE                     # el mismo inicio que usa la conversación: queda ya procesado
    cuerpo = json.dumps({"model": modelo, "system": SISTEMA_BASE, "prompt": "ok", "stream": False,
                         "keep_alive": config.IA_LOCAL_KEEP_ALIVE,
                         "options": {"num_predict": 1, "num_ctx": 2048}}).encode("utf-8")
    try:
        with _ABRIDOR.open(Request(url, data=cuerpo, headers={"Content-Type": "application/json"}, method="POST"),
                           timeout=max(5.0, config.IA_LOCAL_TIMEOUT_S * 2)) as r:
            r.read()
        return True
    except (URLError, TimeoutError, OSError, ValueError):
        return False
