from fastapi import HTTPException

from ..repositorios import tripulantes
from ..repositorios.conexion import get_conn


def conexion():
    conn = get_conn()
    try:
        yield conn
    finally:
        conn.close()


def requerir_tripulante(conn, tid: str) -> None:
    if not tripulantes.existe(conn, tid):
        raise HTTPException(404, "Tripulante no encontrado")
