"""Límites para los puntos que gastan CPU del modelo local (chat, explicación, voz): sin esto, unas pocas peticiones
seguidas saturan la laptop de a bordo. Todo en memoria y sin dependencias; se reinicia con el servidor."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager

from .. import config

_cerrojo = threading.Lock()
_recientes: dict[str, deque] = defaultdict(deque)
_simultaneas = threading.BoundedSemaphore(max(1, config.IA_MAX_SIMULTANEAS))


class LimiteExcedido(Exception):
    def __init__(self, motivo: str, espera_s: int = 5):
        super().__init__(motivo)
        self.motivo, self.espera_s = motivo, espera_s


def contar_peticion(quien: str, ahora: float | None = None) -> None:
    """Ventana de un minuto por persona. Lanza LimiteExcedido si ya pidió demasiado."""
    ahora = time.monotonic() if ahora is None else ahora
    tope = config.IA_PETICIONES_POR_MIN
    if tope <= 0:
        return
    with _cerrojo:
        cola = _recientes[quien]
        while cola and ahora - cola[0] > 60:
            cola.popleft()
        if len(cola) >= tope:
            raise LimiteExcedido("Demasiadas peticiones seguidas; espera un momento.", int(60 - (ahora - cola[0])) + 1)
        cola.append(ahora)


@contextmanager
def lugar_en_el_modelo():
    """Un cupo de trabajo simultáneo con el modelo. Si no hay cupo, falla enseguida en vez de acumular peticiones."""
    if not _simultaneas.acquire(blocking=False):
        raise LimiteExcedido("El asistente está ocupado; inténtalo de nuevo en unos segundos.", 3)
    try:
        yield
    finally:
        _simultaneas.release()


def reiniciar() -> None:
    with _cerrojo:
        _recientes.clear()


def auditar_respuesta_ia(actor_id: str | None, tid: str, ruta: str, respuesta: dict) -> dict:
    """Anota en la auditoría los hechos relevantes de una respuesta de IA, SIN el texto de nadie, y quita la bandera interna.
    - ia_salida_nube: la consulta salió de la estación (DeepSeek).
    - intento_inyeccion: sin identificar a la persona (la heurística puede equivocarse).
    A propósito NO se anota nada de crisis, respiración ni contenido emocional: el comandante lee esta auditoría."""
    from . import auditoria
    if respuesta.pop("sospecha_inyeccion", False):
        auditoria.anotar("sistema", "intento_inyeccion", None, {"ruta": ruta})
    if respuesta.get("fuente") == "deepseek":
        via = "respaldo" if config.IA_PROVEEDOR in {"automatico", "auto"} else "directa"
        auditoria.anotar(actor_id, "ia_salida_nube", tid, {"ruta": ruta, "via": via})
    return respuesta


def auditar_limite(actor_id: str | None, tid: str, ruta: str) -> None:
    from . import auditoria
    auditoria.anotar(actor_id, "limite_ia", tid, {"ruta": ruta})
