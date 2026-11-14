from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..servicios import alertas as servicio_alertas
from ..servicios import estado as servicio_estado
from ..servicios import lecturas as servicio
from ..servicios import auditoria
from ..servicios import preferencias as servicio_preferencias
from ..servicios import recordatorios as servicio_recordatorios
from ..servicios import historial as servicio_historial
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
        estilo = servicio_preferencias.obtener(conn, a["tripulante_id"] or datos.tripulante_id)
        r = servicio.registrar_lectura(conn, datos.tripulante_id, datos.indicador, datos.valor, estilo)
        if a["tripulante_id"] and a["tripulante_id"] != datos.tripulante_id:
            auditoria.registrar(conn, a["tripulante_id"], "lectura_a_tercero", datos.tripulante_id,
                                {"indicador": datos.indicador, "valor": datos.valor})
            conn.commit()
        return r
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/estado/{tid}")
def estado(tid: str, conn=Depends(conexion), a: dict = Depends(requiere("clinico:leer"))) -> dict:
    requerir_tripulante(conn, tid)
    estilo = servicio_preferencias.obtener(conn, a["tripulante_id"] or tid)
    return servicio_estado.estado_tripulante(conn, tid, estilo)


@router.get("/alertas/colectivas")
def alertas_colectivas(conn=Depends(conexion), _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Cruce de CO2 de cabina con el estado de la tripulación."""
    return servicio_alertas.alertas_colectivas(conn)


@router.get("/historial/{tid}")
def historial(tid: str, indicador: str, dias: float = 14, limite: int = 500, conn=Depends(conexion),
              _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Serie temporal de un indicador (para gráficas). El ánimo diario es privado y no sale por aquí."""
    requerir_tripulante(conn, tid)
    try:
        return servicio_historial.serie_indicador(conn, tid, indicador, dias, limite)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/recordatorios")
def recordatorios(conn=Depends(conexion), _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Quién tiene la medición vencida, según su nivel actual y su frecuencia de recordatorios elegida."""
    return servicio_recordatorios.recordatorios_tripulacion(conn)


@router.get("/recordatorios/{tid}")
def recordatorio(tid: str, conn=Depends(conexion), _: dict = Depends(requiere("clinico:leer"))) -> dict:
    requerir_tripulante(conn, tid)
    return servicio_recordatorios.recordatorio_tripulante(conn, tid)
