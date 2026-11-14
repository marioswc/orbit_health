"""Entrada de un flujo continuo de sensores con agrupación por ventanas y paso inmediato de lo extremo.

El estado de las ventanas vive en memoria (un solo proceso). Si el servidor se reinicia, se pierde como mucho una
ventana abierta; lo ya registrado está en la base. Una emergencia nunca espera: un valor extremo se registra al
instante, con un tiempo mínimo entre extremos del mismo indicador para no inundar la cola en una crisis.
"""
from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .. import config
from ..dominio import flujo as reglas_flujo
from ..dominio.catalogos import validar
from . import lecturas


@dataclass
class _Ventana:
    inicio: datetime
    origen: str = "sensor"
    valores: list[float] = field(default_factory=list)


_ventanas: dict[tuple[str, str], _Ventana] = {}
_ultimo_extremo: dict[tuple[str, str], datetime] = {}
_cerrojo = threading.Lock()


def reiniciar() -> None:
    """Vacía el estado en memoria (pruebas)."""
    with _cerrojo:
        _ventanas.clear()
        _ultimo_extremo.clear()


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


ORIGENES = ("sensor", "simulado")


def _registrar(conn, tid: str, indicador: str, valor: float, origen: str = "sensor") -> dict:
    return lecturas.registrar_lectura(conn, tid, indicador, valor, origen=origen)


def ingresar(conn: sqlite3.Connection, tid: str, indicador: str, valor: float,
             ahora: datetime | None = None, origen: str = "sensor") -> dict:
    """Recibe una muestra. Devuelve si se registró una lectura y por qué (extremo, ventana o solo acumulada)."""
    error = validar(indicador, valor)
    if error:
        raise ValueError(error)
    if origen not in ORIGENES:
        raise ValueError(f"origen debe ser uno de: {', '.join(ORIGENES)}")
    ahora = ahora or _ahora()
    clave = (tid, indicador)
    ventana_s, enfriamiento_s = config.FLUJO_VENTANA_S, config.FLUJO_ENFRIAMIENTO_S

    accion, a_registrar, origen_reg = "acumular", None, origen
    with _cerrojo:
        if ventana_s <= 0:
            accion, a_registrar = "sin_agrupar", valor
        elif reglas_flujo.es_extremo(indicador, valor) and (
                clave not in _ultimo_extremo or (ahora - _ultimo_extremo[clave]).total_seconds() >= enfriamiento_s):
            _ultimo_extremo[clave] = ahora
            accion, a_registrar = "extremo", valor
        else:
            v = _ventanas.setdefault(clave, _Ventana(inicio=ahora, origen=origen))
            v.valores.append(valor)
            if (ahora - v.inicio).total_seconds() >= ventana_s:
                accion, a_registrar, origen_reg = "ventana", reglas_flujo.resumir(v.valores), v.origen
                _ventanas.pop(clave, None)
    if a_registrar is None:
        n = len(_ventanas.get(clave, _Ventana(ahora)).valores)
        return {"registrada": False, "motivo": "acumulada", "muestras_en_ventana": n, "lectura": None}
    return {"registrada": True, "motivo": accion, "valor_registrado": a_registrar,
            "lectura": _registrar(conn, tid, indicador, a_registrar, origen_reg)}


def vaciar(conn: sqlite3.Connection, tid: str | None = None) -> dict:
    """Cierra ya las ventanas abiertas (de un tripulante o de todos) y registra su mediana."""
    with _cerrojo:
        claves = [c for c in _ventanas if tid is None or c[0] == tid]
        pendientes = [(c, _ventanas.pop(c)) for c in claves]
    resultados = [{"tripulante_id": c[0], "indicador": c[1], "muestras": len(v.valores),
                   "lectura": _registrar(conn, c[0], c[1], reglas_flujo.resumir(v.valores), v.origen)} for c, v in pendientes if v.valores]
    return {"cerradas": len(resultados), "resultados": resultados}


def ingresar_lote(conn: sqlite3.Connection, tid: str, muestras: list[tuple[str, float]],
                  ahora: datetime | None = None, origen: str = "sensor") -> dict:
    for indicador, valor in muestras:                       # todo o nada: se valida antes de procesar
        error = validar(indicador, valor)
        if error:
            raise ValueError(f"{indicador}: {error}")
    resultados = [ingresar(conn, tid, i, v, ahora, origen) for i, v in muestras]
    registradas = [r for r in resultados if r["registrada"]]
    return {"recibidas": len(resultados), "registradas": len(registradas),
            "motivos": sorted({r["motivo"] for r in registradas}),
            "ultima": registradas[-1]["lectura"] if registradas else None}
