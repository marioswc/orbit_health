"""Perfil personal del asistente: lo que la persona escribe sobre sus intereses y lo que la motiva.

Es texto libre pero acotado: sin saltos de línea ni caracteres de control, con tope de longitud, y siempre se entrega al
modelo como DATO entre comillas. Solo se usa con un modelo LOCAL: nunca se envía a un proveedor externo.
"""
import sqlite3
from datetime import datetime, timezone

from ..repositorios import perfil_ia as repo
from ..repositorios import tripulantes

MAX_CARACTERES = 160


def limpiar(texto: str) -> str:
    t = " ".join((texto or "").split())             # colapsa saltos de línea y espacios
    if any(ord(c) < 32 or ord(c) == 127 for c in t):
        raise ValueError("El texto contiene caracteres no permitidos")
    if len(t) > MAX_CARACTERES:
        raise ValueError(f"Máximo {MAX_CARACTERES} caracteres")
    return t


def obtener(conn: sqlite3.Connection, tid: str) -> dict:
    return {"intereses": repo.obtener(conn, tid)}


def guardar(conn: sqlite3.Connection, tid: str, intereses: str) -> dict:
    repo.guardar(conn, tid, limpiar(intereses), datetime.now(timezone.utc).isoformat())
    conn.commit()
    return obtener(conn, tid)


def contexto(conn: sqlite3.Connection, tid: str) -> dict:
    """Lo que el asistente puede saber de la persona: su nombre y los intereses que ella misma escribió."""
    return {"nombre": tripulantes.nombre(conn, tid), "intereses": repo.obtener(conn, tid)}
