from fastapi import APIRouter, Depends

from ..servicios import estado as servicio_estado
from ..servicios import explicador_local
from .dependencias import conexion, requerir_tripulante, requiere

router = APIRouter(prefix="/api", tags=["asistente"])


@router.get("/estado/{tid}/explicacion")
def explicar_estado(tid: str, conn=Depends(conexion),
                     _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Explica un estado ya calculado con reglas locales o un modelo local opcional."""
    requerir_tripulante(conn, tid)
    estado = servicio_estado.estado_tripulante(conn, tid)
    return explicador_local.explicar(estado)
