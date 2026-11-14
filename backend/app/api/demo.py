from fastapi import APIRouter, Depends, HTTPException

from ..fuentes import escenarios
from .dependencias import conexion, requiere

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/escenarios")
def listar(_: dict = Depends(requiere("demo:ejecutar"))) -> list[dict]:
    return escenarios.listar()


@router.post("/escenarios/{nombre}")
def ejecutar(nombre: str, reconectar: bool = False, conn=Depends(conexion),
             _: dict = Depends(requiere("demo:ejecutar"))) -> dict:
    """Ejecuta un escenario guionizado. Escribe datos de demostración; desactivar con ORBIT_DEMO_API=0."""
    try:
        return escenarios.ejecutar(conn, nombre, reconectar)
    except KeyError:
        raise HTTPException(404, "Escenario desconocido")
