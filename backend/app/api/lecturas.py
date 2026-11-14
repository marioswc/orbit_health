from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..servicios import alertas as servicio_alertas
from ..servicios import estado as servicio_estado
from ..servicios import lecturas as servicio
from .dependencias import conexion, requerir_tripulante

router = APIRouter(prefix="/api", tags=["lecturas"])


class LecturaIn(BaseModel):
    tripulante_id: str
    indicador: str
    valor: float


@router.post("/lecturas")
def crear_lectura(datos: LecturaIn, conn=Depends(conexion)) -> dict:
    requerir_tripulante(conn, datos.tripulante_id)
    try:
        return servicio.registrar_lectura(conn, datos.tripulante_id, datos.indicador, datos.valor)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/estado/{tid}")
def estado(tid: str, conn=Depends(conexion)) -> dict:
    requerir_tripulante(conn, tid)
    return servicio_estado.estado_tripulante(conn, tid)


@router.get("/alertas/colectivas")
def alertas_colectivas(conn=Depends(conexion)) -> dict:
    """Cruce de CO2 de cabina con el estado de la tripulación."""
    return servicio_alertas.alertas_colectivas(conn)
