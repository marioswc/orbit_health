from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dominio import guardia_ia
from ..servicios import estado as servicio_estado
from ..servicios import perfil_ia as servicio
from ..servicios import preferencias as servicio_preferencias
from ..servicios import voz_local
from .dependencias import actor, conexion, exigir_propietario, requerir_tripulante

router = APIRouter(prefix="/api", tags=["asistente"])


class PerfilIn(BaseModel):
    intereses: str | None = Field(default=None, max_length=400)
    rasgos: str | None = Field(default=None, max_length=400)


class MensajeIn(BaseModel):
    rol: str = Field(pattern="^(yo|asistente)$")
    texto: str = Field(max_length=300)


class ChatIn(BaseModel):
    texto: str = Field(min_length=1, max_length=500)
    idioma: str | None = Field(default=None, pattern="^(es|en)$")      # si no se indica, se detecta del texto
    historial: list[MensajeIn] = Field(default_factory=list, max_length=6)   # últimos mensajes; el servidor no los guarda


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
        return servicio.guardar(conn, tid, datos.intereses, datos.rasgos)
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
                            perfil=ctx["intereses"], rasgos=ctx["rasgos"], nombre=(ctx["nombre"].split() or [""])[0],
                            idioma=datos.idioma or guardia_ia.detectar_idioma(datos.texto),
                            historial=[m.model_dump() for m in datos.historial])
    r["nivel_general"] = estado["nivel_general"]
    return r


@router.get("/asistente/saludo/{tid}")
def saludo(tid: str, idioma: str = "es", conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Saludo de Nova y atajos de conversación (sin modelo). Privado: solo el propio astronauta."""
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)
    ctx = servicio.contexto(conn, tid)
    tono = servicio_preferencias.obtener(conn, tid).get("tono", "directo")
    return voz_local.saludo(ctx["nombre"].split()[0] if ctx["nombre"] else "", ctx["intereses"], tono, "en" if idioma == "en" else "es")
