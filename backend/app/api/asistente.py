from fastapi import APIRouter, Depends

from ..servicios import estado as servicio_estado
from ..servicios import explicador_local, limites
from ..servicios import preferencias as servicio_preferencias
from fastapi import HTTPException

from .dependencias import conexion, requerir_tripulante, requiere

router = APIRouter(prefix="/api", tags=["asistente"])


@router.get("/estado/{tid}/explicacion")
def explicar_estado(tid: str, conn=Depends(conexion),
                     _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Explica un estado ya calculado con reglas locales o un modelo local opcional."""
    requerir_tripulante(conn, tid)
    estado = servicio_estado.estado_tripulante(conn, tid)
    try:
        limites.contar_peticion(f"explicacion:{tid}")
        with limites.lugar_en_el_modelo():
            return explicador_local.explicar(estado, servicio_preferencias.obtener(conn, tid))   # se adapta a lo que el tripulante eligió
    except limites.LimiteExcedido as e:
        raise HTTPException(429, e.motivo, headers={"Retry-After": str(e.espera_s)}) from e
