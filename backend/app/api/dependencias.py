from fastapi import Depends, Header, HTTPException

from .. import config
from ..dominio import seguridad as seg
from ..repositorios import tripulantes
from ..repositorios.conexion import get_conn
from ..servicios import auth

SISTEMA = {"tripulante_id": None, "rol": "sistema"}


def conexion():
    conn = get_conn()
    try:
        yield conn
    finally:
        conn.close()


def requerir_tripulante(conn, tid: str) -> None:
    if not tripulantes.existe(conn, tid):
        raise HTTPException(404, "Tripulante no encontrado")


def token_de(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def actor(authorization: str | None = Header(default=None), conn=Depends(conexion)) -> dict:
    """Quién hace la petición. Con la autenticación desactivada (demo en una estación) actúa 'sistema'."""
    if not config.AUTH_ACTIVA:
        return SISTEMA
    s = auth.sesion(conn, token_de(authorization))
    if not s:
        raise HTTPException(401, "Sesión requerida o vencida", headers={"WWW-Authenticate": "Bearer"})
    return s


def requiere(accion: str):
    """Exige que el rol del actor tenga permiso para la acción."""
    def dependencia(a: dict = Depends(actor)) -> dict:
        if a is not SISTEMA and not seg.permitido(a["rol"], accion):
            raise HTTPException(403, "Tu rol no permite esta acción")
        return a
    return dependencia


def exigir_propietario(a: dict, tid: str) -> None:
    """Diario y PHQ-2 son exclusivos de su dueño, sin excepción de rol."""
    if a is not SISTEMA and a["tripulante_id"] != tid:
        raise HTTPException(403, "Solo el propio tripulante puede acceder a sus datos personales")
