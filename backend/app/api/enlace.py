from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..repositorios import enlace as repo
from ..servicios import cola as servicio
from ..servicios import auditoria
from .dependencias import conexion, requiere

router = APIRouter(prefix="/api", tags=["enlace"])


class EnlaceIn(BaseModel):
    activo: bool
    entorno: str = "marte"


@router.get("/enlace")
def ver_enlace(conn=Depends(conexion), _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Estado actual del enlace con Tierra (activo o eclipse, y entorno)"""
    return repo.leer(conn)


@router.post("/enlace")
def cambiar_enlace(datos: EnlaceIn, conn=Depends(conexion), a: dict = Depends(requiere("enlace:cambiar"))) -> dict:
    """Cambia el estado o el entorno del enlace y despacha lo retenido si hay enlace"""
    try:
        r = servicio.cambiar_enlace(conn, datos.activo, datos.entorno)
        auditoria.registrar(conn, a["tripulante_id"], "enlace_cambio", None,
                            {"activo": datos.activo, "entorno": datos.entorno})
        conn.commit()
        return r
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/enlace/latencia")
def latencia(conn=Depends(conexion), _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Perfil de retardo en uso, factor de aceleración y eventos en tránsito."""
    return servicio.info_latencia(conn)


@router.get("/cola")
def cola(conn=Depends(conexion), _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Cola de salida: resumen por estado y eventos recientes"""
    return servicio.estado_cola(conn)


@router.get("/cola/verificar")
def verificar(conn=Depends(conexion), _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Comprueba que la cadena de hash de la cola no fue alterada"""
    return servicio.verificar_cadena(conn)


@router.get("/tierra/mensajes")
def mensajes_en_tierra(limite: int = 200, conn=Depends(conexion),
                       _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Vista del centro de control: solo lo que ya llegó por la hora estimada, lo urgente primero.
    Solo lectura: no consume mensajes. (Tierra no tiene rol propio; en la demo lo ve cualquier sesión.)"""
    return servicio.vista_tierra(conn, limite=limite)
