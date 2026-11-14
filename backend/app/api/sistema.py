from fastapi import APIRouter, Depends, Request

from ..dominio.catalogos import INDICADORES
from ..dominio import peligros as dominio_peligros
from ..dominio.umbrales import UMBRALES
from ..repositorios import tripulantes
from ..servicios import recuperacion
from .dependencias import conexion

router = APIRouter(prefix="/api", tags=["sistema"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/salud")
def salud(request: Request) -> dict:
    """Estado de la base y de los respaldos. Pensado para que un tripulante no técnico sepa si todo está bien."""
    return recuperacion.estado_salud(arranque=getattr(request.app.state, "arranque", None))


@router.get("/umbrales")
def umbrales_estado() -> dict:
    """Versión y estado de validación clínica de los umbrales en uso."""
    return {"version": UMBRALES["version"], "estado": UMBRALES["estado"]}


@router.get("/indicadores")
def indicadores() -> list[dict]:
    return [{"clave": k, "etiqueta": v[0], "unidad": v[1], "min": v[2], "max": v[3]}
            for k, v in INDICADORES.items()]


@router.get("/peligros")
def peligros() -> dict:
    """Marco de peligros y riesgos del HRP, con la cobertura real de ORBIT Health por cada riesgo."""
    return {**dominio_peligros.DATOS, "resumen_cobertura": dominio_peligros.resumen_cobertura()}


@router.get("/tripulantes")
def listar_tripulantes(conn=Depends(conexion)) -> list[dict]:
    return tripulantes.listar(conn)
