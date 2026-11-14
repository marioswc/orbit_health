from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..servicios import bienestar as servicio
from .dependencias import conexion, requerir_tripulante

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
def crear_diario(nota: DiarioIn, conn=Depends(conexion)) -> dict:
    """Guarda en local. Por diseño no escribe en la cola de salida."""
    requerir_tripulante(conn, nota.tripulante_id)
    return servicio.registrar_nota(conn, nota.tripulante_id, nota.titulo, nota.contenido)


@router.get("/diario/{tid}")
def listar_diario(tid: str, conn=Depends(conexion)) -> list[dict]:
    requerir_tripulante(conn, tid)
    return servicio.listar_notas(conn, tid)


@router.post("/tamizajes")
def crear_tamizaje(datos: TamizajeIn, conn=Depends(conexion)) -> dict:
    requerir_tripulante(conn, datos.tripulante_id)
    return servicio.registrar_tamizaje(conn, datos.tripulante_id, datos.item1, datos.item2)
