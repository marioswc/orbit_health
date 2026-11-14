from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..servicios import alertas as servicio_alertas
from ..servicios import estado as servicio_estado
from ..servicios import lecturas as servicio
from ..servicios import auditoria
from .dependencias import conexion, requerir_tripulante, requiere

router = APIRouter(prefix="/api", tags=["lecturas"])


class LecturaIn(BaseModel):
    tripulante_id: str
    indicador: str
    valor: float


@router.post("/lecturas")
def crear_lectura(datos: LecturaIn, conn=Depends(conexion), a: dict = Depends(requiere("clinico:escribir"))) -> dict:
    """Cualquier tripulante autenticado puede registrar signos de un compañero (p. ej. si este queda incapacitado)."""
    requerir_tripulante(conn, datos.tripulante_id)
    try:
        r = servicio.registrar_lectura(conn, datos.tripulante_id, datos.indicador, datos.valor)
        if a["tripulante_id"] and a["tripulante_id"] != datos.tripulante_id:
            auditoria.registrar(conn, a["tripulante_id"], "lectura_a_tercero", datos.tripulante_id,
                                {"indicador": datos.indicador, "valor": datos.valor})
            conn.commit()
        return r
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/estado/{tid}")
def estado(tid: str, conn=Depends(conexion), _: dict = Depends(requiere("clinico:leer"))) -> dict:
    requerir_tripulante(conn, tid)
    return servicio_estado.estado_tripulante(conn, tid)


@router.get("/alertas/colectivas")
def alertas_colectivas(conn=Depends(conexion), _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Cruce de CO2 de cabina con el estado de la tripulación."""
    return servicio_alertas.alertas_colectivas(conn)
