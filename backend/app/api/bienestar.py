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


class AnimoIn(BaseModel):
    tripulante_id: str
    valor: int = Field(ge=1, le=5)


@router.post("/animo")
def crear_animo(datos: AnimoIn, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Ánimo diario de 1 a 5. Exclusivo de su dueño y nunca se transmite."""
    requerir_tripulante(conn, datos.tripulante_id)
    exigir_propietario(a, datos.tripulante_id)
    return servicio.registrar_animo(conn, datos.tripulante_id, datos.valor)


@router.get("/animo/{tid}")
def ver_animo(tid: str, dias: float = 14, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)
    return servicio.serie_animo(conn, tid, dias)
