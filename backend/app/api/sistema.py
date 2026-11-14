from fastapi import APIRouter, Depends

from ..dominio.catalogos import INDICADORES
from ..dominio.umbrales import UMBRALES
from ..repositorios import tripulantes
from .dependencias import conexion

router = APIRouter(prefix="/api", tags=["sistema"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/umbrales")
def umbrales_estado() -> dict:
    """Versión y estado de validación clínica de los umbrales en uso."""
    return {"version": UMBRALES["version"], "estado": UMBRALES["estado"]}


@router.get("/indicadores")
def indicadores() -> list[dict]:
    return [{"clave": k, "etiqueta": v[0], "unidad": v[1], "min": v[2], "max": v[3]}
            for k, v in INDICADORES.items()]


@router.get("/tripulantes")
def listar_tripulantes(conn=Depends(conexion)) -> list[dict]:
    return tripulantes.listar(conn)
