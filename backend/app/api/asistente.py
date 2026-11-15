from fastapi import APIRouter, Depends

from ..servicios import estado as servicio_estado
from ..servicios import explicador_local, limites
from ..servicios import preferencias as servicio_preferencias
from fastapi import HTTPException

from .dependencias import conexion, requerir_tripulante, requiere

router = APIRouter(prefix="/api", tags=["asistente"])


@router.get("/estado/{tid}/explicacion")
def explicar_estado(tid: str, conn=Depends(conexion),
                     a: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Explica un estado ya calculado con reglas locales o un modelo local opcional."""
    requerir_tripulante(conn, tid)
    estado = servicio_estado.estado_tripulante(conn, tid)
    try:
        limites.contar_peticion(f"explicacion:{tid}")
        with limites.lugar_en_el_modelo():
            r = explicador_local.explicar(estado, servicio_preferencias.obtener(conn, tid))   # se adapta a lo que el tripulante eligió
    except limites.LimiteExcedido as e:
        limites.auditar_limite(a.get("tripulante_id"), tid, "explicacion")
        raise HTTPException(429, e.motivo, headers={"Retry-After": str(e.espera_s)}) from e
    return limites.auditar_respuesta_ia(a.get("tripulante_id"), tid, "explicacion", r)
