"""Perfil personal del asistente: lo que la persona escribe sobre sus intereses y lo que la motiva.

Es texto libre pero acotado: sin saltos de línea ni caracteres de control, con tope de longitud, y siempre se entrega al
modelo como DATO entre comillas. Solo se usa con un modelo LOCAL: nunca se envía a un proveedor externo.
"""
import sqlite3
from datetime import datetime, timezone

from ..dominio import guardia_ia
from ..repositorios import perfil_ia as repo
from ..repositorios import tripulantes

MAX_CARACTERES = 160


def limpiar(texto: str) -> str:
    bruto = texto or ""
    if any((ord(c) < 32 and c not in "\n\t\r") or ord(c) == 127 for c in bruto):
        raise ValueError("El texto contiene caracteres no permitidos")
    t = guardia_ia.sanear_para_prompt(bruto, MAX_CARACTERES + 1)      # sin marcas de plantilla ni encabezados de rol
    if len(t) > MAX_CARACTERES:
        raise ValueError(f"Máximo {MAX_CARACTERES} caracteres")
    return t


def obtener(conn: sqlite3.Connection, tid: str) -> dict:
    return repo.obtener(conn, tid)


def guardar(conn: sqlite3.Connection, tid: str, intereses: str | None = None, rasgos: str | None = None) -> dict:
    """Guarda lo que se indique; lo que viene como None se conserva."""
    actual = repo.obtener(conn, tid)
    nuevo_i = actual["intereses"] if intereses is None else limpiar(intereses)
    nuevo_r = actual["rasgos"] if rasgos is None else limpiar(rasgos)
    repo.guardar(conn, tid, nuevo_i, nuevo_r, datetime.now(timezone.utc).isoformat())
    conn.commit()
    return obtener(conn, tid)


def contexto(conn: sqlite3.Connection, tid: str) -> dict:
    """Lo que el asistente puede saber de la persona: su nombre y lo que ella misma escribió de sí."""
    return {"nombre": tripulantes.nombre(conn, tid), **repo.obtener(conn, tid)}
