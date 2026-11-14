"""Preferencias del asistente. Solo se guarda lo que el tripulante elige de forma explícita."""
import sqlite3
from datetime import datetime, timezone

from ..dominio.acciones import DETALLES, ESTILO_POR_DEFECTO, RECORDATORIOS, TONOS
from ..repositorios import preferencias as repo


def obtener(conn: sqlite3.Connection, tid: str | None) -> dict:
    if not tid:
        return dict(ESTILO_POR_DEFECTO)
    return {**ESTILO_POR_DEFECTO, **(repo.obtener(conn, tid) or {})}


def guardar(conn: sqlite3.Connection, tid: str, tono: str, detalle: str, recordatorios: str) -> dict:
    for valor, validos, nombre in ((tono, TONOS, "tono"), (detalle, DETALLES, "detalle"),
                                   (recordatorios, RECORDATORIOS, "recordatorios")):
        if valor not in validos:
            raise ValueError(f"{nombre} debe ser uno de: {', '.join(validos)}")
    repo.guardar(conn, tid, tono, detalle, recordatorios, datetime.now(timezone.utc).isoformat())
    conn.commit()
    return obtener(conn, tid)
