from fastapi import APIRouter, Body, Depends, Header, HTTPException

from .. import config
from ..servicios import estado as servicio_estado
from ..servicios import limites
from ..servicios import perfil_ia as servicio_perfil
from ..servicios import preferencias as servicio_preferencias
from ..servicios import voz_local
from .dependencias import actor, conexion, exigir_propietario, requerir_tripulante, requiere

router = APIRouter(prefix="/api/voz", tags=["voz"])


@router.post("/chat/{tid}")
def chat_voz(tid: str, audio: bytes = Body(...), idioma: str = "auto", content_type: str | None = Header(default=None),
             content_length: int | None = Header(default=None),
             conn=Depends(conexion), a: dict = Depends(actor), _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Transcribe audio localmente, responde con el LLM local y devuelve audio opcional."""
    if not config.VOZ_ACTIVA:
        raise HTTPException(503, "La voz local está desactivada")
    if content_length is not None and content_length > config.VOZ_MAX_AUDIO_BYTES:
        raise HTTPException(413, "Audio demasiado grande")
    requerir_tripulante(conn, tid)
    exigir_propietario(a, tid)               # la conversación es personal: solo su dueño
    try:
        limites.contar_peticion(f"voz:{tid}")
    except limites.LimiteExcedido as e:
        limites.auditar_limite(a.get("tripulante_id"), tid, "voz")
        raise HTTPException(429, e.motivo, headers={"Retry-After": str(e.espera_s)}) from e
    extension = ".wav" if not content_type else {
        "audio/wav": ".wav", "audio/webm": ".webm", "audio/ogg": ".ogg",
        "audio/mpeg": ".mp3", "audio/mp4": ".m4a",
    }.get(content_type.split(";", 1)[0].lower(), ".wav")
    if not voz_local.adquirir_trabajo():
        raise HTTPException(429, "La capacidad de voz está ocupada; inténtalo de nuevo")
    try:
        idioma_solicitado = voz_local.normalizar_idioma(idioma)
        texto, idioma_real = voz_local.transcribir_con_idioma(audio, extension, idioma_solicitado)
        estado = servicio_estado.estado_tripulante(conn, tid)
        preferencias = servicio_preferencias.obtener(conn, tid)
        ctx = servicio_perfil.contexto(conn, tid)
        respuesta = voz_local.responder(texto, estado, preferencias, perfil=ctx["intereses"], rasgos=ctx["rasgos"], nombre=(ctx["nombre"].split() or [""])[0], idioma=idioma_real)
        respuesta["transcripcion"] = texto
        limites.auditar_respuesta_ia(a.get("tripulante_id"), tid, "voz", respuesta)
        respuesta["nivel_general"] = estado["nivel_general"]
        if config.VOZ_PIPER_MODELO:
            respuesta["audio_base64"] = voz_local.sintetizar(respuesta["texto"], idioma_real)
            respuesta["audio_media_type"] = "audio/wav"
        return respuesta
    except voz_local.VozNoDisponible as error:
        raise HTTPException(503, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    finally:
        voz_local.liberar_trabajo()
