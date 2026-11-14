"""Línea de tiempo "con y sin ORBIT" ante un mismo evento. Es una ILUSTRACIÓN del dilema, no una medición.

Supuestos explícitos: el retardo viene de datos/enlace.json y el tiempo que Tierra tarda en leer y responder
es un parámetro (no hay datos reales de ello). Sin ORBIT se asume que la tripulación no tiene clasificación
automática ni acciones sugeridas a bordo.
"""
from __future__ import annotations

from typing import Sequence


def linea_de_tiempo(retardo_s: float, respuesta_tierra_s: float, nivel: str, acciones: Sequence[str],
                    factor_aceleracion: float = 1.0) -> dict:
    """Todos los tiempos están en segundos desde el evento. `demo` aplica el factor de aceleración."""
    llega = retardo_s
    acuse = 2 * retardo_s
    respuesta = 2 * retardo_s + respuesta_tierra_s

    def ev(t: float, texto: str) -> dict:
        return {"t_s": round(t, 1), "t_demo_s": round(t / factor_aceleracion, 2), "texto": texto}

    con = [
        ev(0, f"La lectura se registra y se clasifica a bordo: nivel {nivel}."),
        ev(0, "El sistema muestra qué hacer ahora: " + " ".join(acciones[:2])),
        ev(0, "El evento entra a la cola con su prioridad; si hay enlace, sale de inmediato y primero."),
        ev(llega, "El evento llega a Tierra."),
        ev(acuse, "Vuelve a la nave la confirmación de recepción."),
        ev(respuesta, "Llega la respuesta de Tierra, cuando ya se llevaba todo ese tiempo actuando a bordo."),
    ]
    sin = [
        ev(0, "El tripulante nota algo y debe decidir por su cuenta, sin clasificación ni pasos sugeridos."),
        ev(llega, "Tierra recibe el aviso, suponiendo que alguien lo redactó y lo envió al instante."),
        ev(respuesta, "Llega la respuesta de Tierra."),
    ]
    return {
        "tipo": "ilustracion",
        "aviso": "Narración con supuestos, no una medición de lo que haría una tripulación sin el sistema.",
        "ventana_sin_apoyo_s": round(respuesta, 1),
        "ventana_sin_apoyo_min": round(respuesta / 60, 1),
        "con_orbit": con,
        "sin_orbit": sin,
    }
