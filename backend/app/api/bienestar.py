from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..servicios import bienestar as servicio
from ..servicios import preferencias as servicio_preferencias
from .dependencias import actor, conexion, exigir_propietario, requerir_tripulante, requiere

router = APIRouter(prefix="/api", tags=["bienestar"])


class DiarioIn(BaseModel):
    tripulante_id: str
    titulo: str | None = None
    contenido: str = Field(min_length=1)


class TamizajeIn(BaseModel):
    tripulante_id: str
    item1: int = Field(ge=0, le=3)
    item2: int = Field(ge=0, le=3)
    riesgo_autolesion: bool = False
    calidad_oxigeno: float | None = None
    compartir_medico: bool = False
    mensaje_medico: str | None = Field(default=None, max_length=280)


class AvisoMedicoIn(BaseModel):
    tripulante_id: str
    consentimiento: bool
    tipo: str = "crisis"
    tamizaje_id: int | None = None
    mensaje: str | None = Field(default=None, max_length=280)


class RevocarAvisoIn(BaseModel):
    tripulante_id: str


@router.post("/diario")
def crear_diario(nota: DiarioIn, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Guarda en local. Por diseño no escribe en la cola de salida."""
    requerir_tripulante(conn, nota.tripulante_id)
    exigir_propietario(a, nota.tripulante_id)
    return servicio.registrar_nota(conn, nota.tripulante_id, nota.titulo, nota.contenido)


@router.get("/diario/{tid}")
def listar_diario(tid: str, conn=Depends(conexion), a: dict = Depends(actor)) -> list[dict]:
    """Notas del diario del propio tripulante (privado)"""
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)
    return servicio.listar_notas(conn, tid)


@router.post("/tamizajes")
def crear_tamizaje(datos: TamizajeIn, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Registra un PHQ-2 y, si procede, devuelve el protocolo de apoyo (privado)"""
    requerir_tripulante(conn, datos.tripulante_id)
    exigir_propietario(a, datos.tripulante_id)
    try:
        return servicio.registrar_tamizaje(
            conn, datos.tripulante_id, datos.item1, datos.item2,
            datos.riesgo_autolesion, datos.compartir_medico, datos.mensaje_medico, datos.calidad_oxigeno,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/crisis/protocolo")
def ver_protocolo_crisis(tripulante_id: str | None = None, nivel: str = "crisis",
                         calidad_oxigeno: float | None = None,
                         conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Protocolo de crisis psicológica / riesgo de autolesión, integrando tono y calidad de oxígeno en cabina."""
    if tripulante_id:
        requerir_tripulante(conn, tripulante_id)
        exigir_propietario(a, tripulante_id)
    try:
        return servicio.obtener_protocolo(conn, tripulante_id, nivel, calidad_oxigeno)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.post("/crisis/aviso-medico")
def crear_aviso_medico(datos: AvisoMedicoIn, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Notifica al médico de a bordo con consentimiento explícito. Nunca entra a la cola hacia Tierra."""
    requerir_tripulante(conn, datos.tripulante_id)
    exigir_propietario(a, datos.tripulante_id)
    try:
        return servicio.solicitar_apoyo_medico(
            conn, datos.tripulante_id, datos.consentimiento, datos.tipo, datos.tamizaje_id, datos.mensaje,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    except LookupError as e:
        raise HTTPException(404, str(e))


@router.get("/crisis/avisos/{tid}")
def ver_mis_avisos(tid: str, conn=Depends(conexion), a: dict = Depends(actor)) -> list[dict]:
    """Avisos que el propio tripulante compartió con el médico y su estado (pendiente, atendido o revocado)."""
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)
    return servicio.listar_mis_avisos(conn, tid)


@router.post("/crisis/avisos/{aviso_id}/revocar")
def revocar_aviso(aviso_id: int, datos: RevocarAvisoIn, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """El propio tripulante revoca su consentimiento: el aviso deja de ser visible para el médico."""
    requerir_tripulante(conn, datos.tripulante_id)
    exigir_propietario(a, datos.tripulante_id)
    try:
        return servicio.revocar_apoyo_medico(conn, datos.tripulante_id, aviso_id)
    except LookupError as e:
        raise HTTPException(404, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))


@router.get("/crisis/avisos")
def listar_avisos_medico(solo_pendientes: bool = False,
                         _: dict = Depends(requiere("salud_mental:avisos")),
                         conn=Depends(conexion)) -> list[dict]:
    """Vista exclusiva para el médico o comandante: solo muestra avisos con consentimiento vigente."""
    return servicio.listar_avisos_medico(conn, solo_pendientes)


@router.post("/crisis/avisos/{aviso_id}/atender")
def atender_aviso_medico(aviso_id: int,
                         a: dict = Depends(requiere("salud_mental:avisos")),
                         conn=Depends(conexion)) -> dict:
    """El médico o el comandante marca un aviso de salud mental como atendido"""
    try:
        return servicio.atender_aviso_medico(conn, aviso_id, a.get("tripulante_id"))
    except LookupError as e:
        raise HTTPException(404, str(e))


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
    """Serie del ánimo diario del propio tripulante (privado)"""
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)
    return servicio.serie_animo(conn, tid, dias)


class PreferenciasIn(BaseModel):
    tono: str = "directo"
    detalle: str = "completo"
    recordatorios: str = "normal"


@router.get("/preferencias/{tid}")
def ver_preferencias(tid: str, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Cómo quiere cada tripulante que le hable el asistente. Solo cambia la forma, nunca el nivel de alerta."""
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)
    return servicio_preferencias.obtener(conn, tid)


@router.put("/preferencias/{tid}")
def guardar_preferencias(tid: str, datos: PreferenciasIn, conn=Depends(conexion), a: dict = Depends(actor)) -> dict:
    """Guarda el tono, el detalle y los recordatorios elegidos por el tripulante"""
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)
    try:
        return servicio_preferencias.guardar(conn, tid, datos.tono, datos.detalle, datos.recordatorios)
    except ValueError as e:
        raise HTTPException(422, str(e))
