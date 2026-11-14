from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..repositorios import enlace as repo
from ..servicios import cola as servicio
from .dependencias import conexion

router = APIRouter(prefix="/api", tags=["enlace"])


class EnlaceIn(BaseModel):
    activo: bool
    entorno: str = "marte"


@router.get("/enlace")
def ver_enlace(conn=Depends(conexion)) -> dict:
    return repo.leer(conn)


@router.post("/enlace")
def cambiar_enlace(datos: EnlaceIn, conn=Depends(conexion)) -> dict:
    try:
        return servicio.cambiar_enlace(conn, datos.activo, datos.entorno)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/enlace/latencia")
def latencia(conn=Depends(conexion)) -> dict:
    """Perfil de retardo en uso, factor de aceleración y eventos en tránsito."""
    return servicio.info_latencia(conn)


@router.get("/cola")
def cola(conn=Depends(conexion)) -> dict:
    return servicio.estado_cola(conn)


@router.get("/cola/verificar")
def verificar(conn=Depends(conexion)) -> dict:
    return servicio.verificar_cadena(conn)
