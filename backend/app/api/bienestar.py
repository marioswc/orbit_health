from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..servicios import bienestar as servicio
from .dependencias import actor, conexion, exigir_propietario, requerir_tripulante

router = APIRouter(prefix="/api", tags=["bienestar"])


class DiarioIn(BaseModel):
    tripulante_id: str
    titulo: str | None = None
    contenido: str = Field(min_length=1)


class TamizajeIn(BaseModel):
    tripulante_id: str
    item1: int = Field(ge=0, le=3)
    item2: int = Field(ge=0, le=3)


@router.post("/diario")
def crear_diario(nota: DiarioIn, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Guarda en local. Por diseño no escribe en la cola de salida."""
    requerir_tripulante(conn, nota.tripulante_id)
    exigir_propietario(a, nota.tripulante_id)
    return servicio.registrar_nota(conn, nota.tripulante_id, nota.titulo, nota.contenido)


@router.get("/diario/{tid}")
def listar_diario(tid: str, conn=Depends(conexion), a: dict = Depends(actor)) -> list[dict]:
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)
    return servicio.listar_notas(conn, tid)


@router.post("/tamizajes")
def crear_tamizaje(datos: TamizajeIn, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    requerir_tripulante(conn, datos.tripulante_id)
    exigir_propietario(a, datos.tripulante_id)
    return servicio.registrar_tamizaje(conn, datos.tripulante_id, datos.item1, datos.item2)
