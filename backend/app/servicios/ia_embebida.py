"""Modelo de lenguaje INCRUSTADO: el motor llama.cpp corre dentro del propio programa, sin Ollama ni ningún servidor aparte.

Se activa con ORBIT_IA_MODELO_GGUF (ruta a un archivo .gguf) y la librería opcional `llama-cpp-python`
(backend/requirements-ia.txt). El ejecutable de doble clic lo configura solo si encuentra un modelo en la carpeta
`modelos` (junto al programa o en la carpeta de datos del usuario). Todo es local: nada sale de la computadora.
Perfil, rasgos y conversación pueden usarse con él porque nunca salen del proceso.
"""
from __future__ import annotations

import importlib.util
import logging
import os
import sys
import threading
from pathlib import Path

from .. import config

log = logging.getLogger("orbit.ia")
_cerrojo = threading.Lock()          # llama.cpp no admite dos generaciones a la vez sobre el mismo contexto
_modelo = None
_fallo: str | None = None


def ruta_del_modelo() -> Path | None:
    r = config.IA_MODELO_GGUF
    return Path(r) if r else None


def _hay_libreria() -> bool:
    if "llama_cpp" in sys.modules:                  # ya importada (o marcada como ausente con None)
        return sys.modules["llama_cpp"] is not None
    try:
        return importlib.util.find_spec("llama_cpp") is not None
    except (ImportError, ValueError):
        return False


def disponible() -> bool:
    """True si hay un archivo .gguf configurado y existe, y la librería está instalada."""
    ruta = ruta_del_modelo()
    return bool(ruta and ruta.is_file() and _hay_libreria() and _fallo is None)


def nombre() -> str:
    ruta = ruta_del_modelo()
    return ruta.stem if ruta else ""


def _cargar():
    global _modelo, _fallo
    if _modelo is None:
        from llama_cpp import Llama
        hilos = config.IA_HILOS or max(1, (os.cpu_count() or 4))
        _modelo = Llama(model_path=str(ruta_del_modelo()), n_ctx=2048, n_threads=hilos, verbose=False)
    return _modelo


def consultar(prompt: str, system: str | None = None, max_tokens: int = 220, temperatura: float = 0.1) -> str | None:
    """Genera una respuesta. Devuelve None si algo falla (el llamador usa su texto de respaldo)."""
    global _fallo
    if not disponible():
        return None
    mensajes = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    try:
        with _cerrojo:
            r = _cargar().create_chat_completion(messages=mensajes, max_tokens=max_tokens, temperature=temperatura)
        texto = (r["choices"][0]["message"]["content"] or "").strip()
        if not texto:
            raise ValueError("el modelo incrustado no devolvió texto")
        return texto[:2000]
    except Exception as error:                      # noqa: BLE001  (archivo dañado, memoria insuficiente, etc.)
        log.warning("El modelo incrustado falló; se usa el texto de respaldo: %s", error)
        _fallo = str(error)[:200]                   # no se reintenta en bucle: se queda sin IA generativa hasta reiniciar
        return None


def precalentar(system: str | None = None) -> bool:
    """Carga el modelo y procesa el inicio fijo del prompt, para que la primera pregunta real sea rápida."""
    if not disponible():
        return False
    return consultar("ok", system, max_tokens=1) is not None


def reiniciar() -> None:
    """Solo para pruebas: olvida el modelo cargado y el último fallo."""
    global _modelo, _fallo
    _modelo, _fallo = None, None
