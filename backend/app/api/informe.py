from fastapi import APIRouter, Depends, Response

from ..servicios import informe as servicio
from .dependencias import conexion, requerir_tripulante, requiere

router = APIRouter(prefix="/api", tags=["informe"])


@router.get("/informe")
def informe_tripulacion(conn=Depends(conexion), _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Resumen de toda la tripulación para Tierra, con huella de integridad. Sin datos personales privados."""
    return servicio.informe_tripulacion(conn)


@router.get("/informe/{tid}")
def informe_tripulante(tid: str, limite: int = 50, formato: str = "json", conn=Depends(conexion),
                       _: dict = Depends(requiere("clinico:leer"))):
    """Informe de un tripulante. `formato=csv` devuelve solo las lecturas, listas para una hoja de cálculo."""
    requerir_tripulante(conn, tid)
    if formato == "csv":
        return Response(servicio.lecturas_csv(conn, tid, limite), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="orbit_{tid}.csv"'})
    return servicio.informe_tripulante(conn, tid, limite)
