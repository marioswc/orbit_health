from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from .. import config
from ..servicios import auditoria, auth
from .dependencias import actor, conexion, requiere, token_de

router = APIRouter(prefix="/api", tags=["seguridad"])


class LoginIn(BaseModel):
    tripulante_id: str
    pin: str


class RecuperarIn(BaseModel):
    tripulante_id: str
    codigo_recuperacion: str
    pin_nuevo: str = Field(min_length=6, max_length=10)


def _error(e: auth.AuthError) -> HTTPException:
    if e.codigo == "bloqueado":
        return HTTPException(423, {"mensaje": str(e), "bloqueado_hasta": e.hasta})
    if e.codigo == "permiso":
        return HTTPException(403, str(e))
    return HTTPException(401, str(e))


@router.get("/auth/estado")
def estado_auth() -> dict:
    """Permite al frontend saber si debe mostrar la pantalla de acceso."""
    return {"activa": config.AUTH_ACTIVA, "sesion_horas": config.SESION_HORAS}


@router.post("/auth/login")
def login(datos: LoginIn, conn=Depends(conexion)) -> dict:
    """Inicia sesión con el PIN y devuelve un token"""
    try:
        return auth.login(conn, datos.tripulante_id, datos.pin)
    except auth.AuthError as e:
        raise _error(e)


@router.post("/auth/logout")
def logout(authorization: str | None = Header(default=None), a: dict = Depends(actor), conn=Depends(conexion)) -> dict:
    """Cierra la sesión actual"""
    token = token_de(authorization)
    if token:
        auth.logout(conn, token, a["tripulante_id"])
    return {"ok": True}


@router.get("/auth/yo")
def yo(a: dict = Depends(actor)) -> dict:
    """Quién es el usuario de la sesión actual y cuál es su rol"""
    return a


@router.post("/auth/recuperar")
def recuperar(datos: RecuperarIn, conn=Depends(conexion)) -> dict:
    """Restablece el PIN con el código de recuperación"""
    try:
        return auth.recuperar(conn, datos.tripulante_id, datos.codigo_recuperacion, datos.pin_nuevo)
    except auth.AuthError as e:
        raise _error(e)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.post("/auth/reiniciar-pin/{tid}")
def reiniciar_pin(tid: str, a: dict = Depends(requiere("pin:reiniciar")), conn=Depends(conexion)) -> dict:
    """El médico o el comandante reinicia el PIN de otro tripulante"""
    try:
        return auth.reiniciar_pin(conn, a, tid)
    except auth.AuthError as e:
        raise _error(e)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/auditoria")
def ver_auditoria(_: dict = Depends(requiere("auditoria:leer")), conn=Depends(conexion)) -> list[dict]:
    """Últimos registros de auditoría (médico o comandante)"""
    return auditoria.recientes(conn)


@router.get("/auditoria/verificar")
def verificar_auditoria(_: dict = Depends(requiere("auditoria:leer")), conn=Depends(conexion)) -> dict:
    """Comprueba que la cadena de hash de la auditoría no fue alterada"""
    return auditoria.verificar(conn)
