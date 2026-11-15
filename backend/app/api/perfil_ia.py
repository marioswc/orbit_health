from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..servicios import estado as servicio_estado
from ..servicios import perfil_ia as servicio
from ..servicios import preferencias as servicio_preferencias
from ..servicios import voz_local
from .dependencias import actor, conexion, exigir_propietario, requerir_tripulante

router = APIRouter(prefix="/api", tags=["asistente"])


class PerfilIn(BaseModel):
    intereses: str = Field(default="", max_length=400)


class ChatIn(BaseModel):
    texto: str = Field(min_length=1, max_length=500)


@router.get("/perfil-ia/{tid}")
def ver_perfil(tid: str, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Intereses que el propio astronauta le cuenta a su asistente (privado: solo su dueño)"""
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)
    return servicio.obtener(conn, tid)


@router.put("/perfil-ia/{tid}")
def guardar_perfil(tid: str, datos: PerfilIn, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Guarda sus intereses y motivadores (máx. 160 caracteres). Solo se usan con un modelo local."""
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)
    try:
        return servicio.guardar(conn, tid, datos.intereses)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@router.post("/asistente/chat/{tid}")
def chat_texto(tid: str, datos: ChatIn, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Conversa por texto con tu asistente de apoyo. Privado: solo el propio astronauta. No requiere la voz."""
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)
    estado = servicio_estado.estado_tripulante(conn, tid)
    ctx = servicio.contexto(conn, tid)
    r = voz_local.responder(datos.texto, estado, servicio_preferencias.obtener(conn, tid),
                            perfil=ctx["intereses"], nombre=ctx["nombre"])
    r["nivel_general"] = estado["nivel_general"]
    return r
