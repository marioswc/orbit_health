"""Modelo de lenguaje INCRUSTADO: el motor llama.cpp corre dentro del propio programa, sin Ollama ni ningún servidor aparte.

Se activa con ORBIT_IA_MODELO_GGUF (ruta a un archivo .gguf) y la librería opcional `llama-cpp-python`
(backend/requirements-ia.txt). El ejecutable de doble clic lo configura solo si encuentra un modelo en la carpeta
`modelos` (junto al programa o en la carpeta de datos del usuario). Todo es local: nada sale de la computadora.
Perfil, rasgos y conversación pueden usarse con él porque nunca salen del proceso.
"""
from __future__ import annotations

import gc
import importlib.util
import logging
import sys
import threading
import time
from pathlib import Path

from .. import config
from . import recursos

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


_fallos_seguidos = 0
_ultimo_uso = 0.0
_vigilante_activo = False
_FALLOS_PARA_DESACTIVAR = 3


def hilos() -> int:
    """0 en la configuración = automático: los núcleos FÍSICOS. Usar los hilos lógicos (hyper-threading) sobrecarga el procesador:
    en el equipo de desarrollo (4 núcleos, 8 hilos) con 4 hilos las respuestas fueron de 2 a 5 veces más rápidas que con 8."""
    return config.IA_HILOS or recursos.nucleos_fisicos()


def _cargar():
    global _modelo
    if _modelo is None:
        from llama_cpp import Llama
        h = hilos()
        _modelo = Llama(model_path=str(ruta_del_modelo()), n_ctx=2048, n_threads=h, n_threads_batch=h, verbose=False)
        log.info("Modelo incrustado cargado con %d hilos (memoria libre: %s MB)", h, recursos.memoria().get("disponible_mb"))
        _iniciar_vigilante()
    return _modelo


def liberar_si_inactivo(ahora: float | None = None) -> bool:
    """Libera la memoria del modelo si lleva sin usarse ORBIT_IA_DESCARGA_MIN minutos. Devuelve True si lo liberó. Nunca interrumpe
    una respuesta en curso (si el cerrojo está ocupado, lo deja para la próxima revisión)."""
    global _modelo
    limite = config.IA_DESCARGA_MIN
    if limite <= 0 or _modelo is None:
        return False
    if (time.monotonic() if ahora is None else ahora) - _ultimo_uso < limite * 60:
        return False
    if not _cerrojo.acquire(blocking=False):
        return False
    try:
        if _modelo is None:
            return False
        cerrar = getattr(_modelo, "close", None)
        if callable(cerrar):
            cerrar()
        _modelo = None
        gc.collect()
        log.info("Modelo incrustado liberado por inactividad (%.0f min sin uso)", limite)
        return True
    finally:
        _cerrojo.release()


def _iniciar_vigilante() -> None:
    global _vigilante_activo
    if _vigilante_activo:
        return
    _vigilante_activo = True

    def vigilar() -> None:
        while True:
            time.sleep(max(1.0, min(30.0, config.IA_DESCARGA_MIN * 30)))
            try:
                liberar_si_inactivo()
            except Exception:                                # noqa: BLE001  el vigilante nunca debe morir ni molestar
                log.exception("Falló la revisión de inactividad del modelo incrustado")
    threading.Thread(target=vigilar, name="ia-vigilante", daemon=True).start()


def consultar(prompt: str, system: str | None = None, max_tokens: int = 220, temperatura: float = 0.1) -> str | None:
    """Genera una respuesta con un límite de tiempo real (ORBIT_IA_EMBEBIDA_TIMEOUT_S). Devuelve None si no se pudo: el llamador usa su texto
    de respaldo. Un tiempo agotado o un fallo puntual NO desactivan la IA; tres fallos seguidos, o un modelo que no carga, sí."""
    global _fallo, _fallos_seguidos, _ultimo_uso
    if not disponible():
        return None
    mensajes = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    try:
        with _cerrojo:
            try:
                modelo = _cargar()
            except Exception as error:                      # noqa: BLE001  archivo dañado o memoria insuficiente: no tiene sentido reintentar
                log.warning("No se pudo cargar el modelo incrustado: %s", error)
                _fallo = str(error)[:200]
                return None
            limite = time.monotonic() + config.IA_EMBEBIDA_TIMEOUT_S
            partes: list[str] = []
            for trozo in modelo.create_chat_completion(messages=mensajes, max_tokens=max_tokens, temperature=temperatura, stream=True):
                parte = trozo["choices"][0]["delta"].get("content")
                if parte:
                    partes.append(parte)
                if time.monotonic() > limite:
                    raise TimeoutError(f"más de {config.IA_EMBEBIDA_TIMEOUT_S:g} s generando")
        texto = "".join(partes).strip()
        if not texto:
            raise ValueError("el modelo incrustado no devolvió texto")
        _fallos_seguidos = 0
        _ultimo_uso = time.monotonic()
        return texto[:2000]
    except TimeoutError as error:
        _ultimo_uso = time.monotonic()
        log.warning("El modelo incrustado tardó demasiado (%s); se usa el texto de respaldo. Memoria libre: %s MB",
                    error, recursos.memoria().get("disponible_mb"))
        return None
    except Exception as error:                              # noqa: BLE001
        _fallos_seguidos += 1
        log.warning("El modelo incrustado falló (%d de %d): %s", _fallos_seguidos, _FALLOS_PARA_DESACTIVAR, error)
        if _fallos_seguidos >= _FALLOS_PARA_DESACTIVAR:
            _fallo = str(error)[:200]                       # hasta reiniciar: no se reintenta en bucle
        return None


def precalentar(system: str | None = None) -> bool:
    """Carga el modelo y procesa el inicio fijo del prompt, para que la primera pregunta real sea rápida."""
    if not disponible():
        return False
    return consultar("ok", system, max_tokens=1) is not None


def reiniciar() -> None:
    """Solo para pruebas: olvida el modelo cargado, el último fallo y los contadores."""
    global _modelo, _fallo, _fallos_seguidos, _ultimo_uso
    _modelo, _fallo, _fallos_seguidos, _ultimo_uso = None, None, 0, 0.0
