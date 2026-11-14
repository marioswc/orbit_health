from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dominio.catalogos import validar
from ..servicios import flujo as servicio_flujo
from ..servicios import lecturas as servicio
from .dependencias import conexion, requerir_tripulante, requiere

router = APIRouter(prefix="/api/sensores", tags=["sensores"])
MAX_LOTE = 100


class LecturaSensor(BaseModel):
    indicador: str
    valor: float


class LoteIn(BaseModel):
    tripulante_id: str
    dispositivo_id: str | None = Field(default=None, max_length=64)
    lecturas: list[LecturaSensor]


class UnaIn(LecturaSensor):
    tripulante_id: str
    dispositivo_id: str | None = Field(default=None, max_length=64)


@router.post("/lectura")
def lectura_de_sensor(datos: UnaIn, conn=Depends(conexion), _: dict = Depends(requiere("clinico:escribir"))) -> dict:
    """Entrada de un dispositivo: misma clasificación y misma cola que la captura manual, con origen 'sensor'."""
    requerir_tripulante(conn, datos.tripulante_id)
    try:
        return servicio.registrar_lectura(conn, datos.tripulante_id, datos.indicador, datos.valor, origen="sensor")
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.post("/lote")
def lote_de_sensor(datos: LoteIn, conn=Depends(conexion), _: dict = Depends(requiere("clinico:escribir"))) -> dict:
    """Varias lecturas de un dispositivo. Todo o nada: si una es inválida no se guarda ninguna."""
    requerir_tripulante(conn, datos.tripulante_id)
    if not 1 <= len(datos.lecturas) <= MAX_LOTE:
        raise HTTPException(422, f"El lote debe traer entre 1 y {MAX_LOTE} lecturas")
    for i, lec in enumerate(datos.lecturas):
        error = validar(lec.indicador, lec.valor)
        if error:
            raise HTTPException(422, f"Lectura {i + 1}: {error}")
    orden = {"verde": 0, "amarillo": 1, "rojo": 2}
    resultados = [servicio.registrar_lectura(conn, datos.tripulante_id, l.indicador, l.valor, origen="sensor")
                  for l in datos.lecturas]
    peor = max((r["nivel"] for r in resultados), key=orden.__getitem__)
    return {"guardadas": len(resultados), "peor_nivel": peor, "ultimo": resultados[-1],
            "dispositivo_id": datos.dispositivo_id}


class MuestraIn(BaseModel):
    indicador: str
    valor: float


class FlujoIn(BaseModel):
    tripulante_id: str
    dispositivo_id: str | None = Field(default=None, max_length=64)
    muestras: list[MuestraIn]


class VaciarIn(BaseModel):
    tripulante_id: str | None = None


@router.post("/flujo")
def muestra_de_flujo(datos: UnaIn, conn=Depends(conexion), _: dict = Depends(requiere("clinico:escribir"))) -> dict:
    """Una muestra de un flujo continuo (p. ej. una banda): se agrupa por ventanas, salvo los valores extremos"""
    requerir_tripulante(conn, datos.tripulante_id)
    try:
        return servicio_flujo.ingresar(conn, datos.tripulante_id, datos.indicador, datos.valor)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.post("/flujo/lote")
def lote_de_flujo(datos: FlujoIn, conn=Depends(conexion), _: dict = Depends(requiere("clinico:escribir"))) -> dict:
    """Varias muestras de un flujo continuo en una sola petición (hasta 500); todo o nada si alguna es inválida"""
    requerir_tripulante(conn, datos.tripulante_id)
    if not 1 <= len(datos.muestras) <= 500:
        raise HTTPException(422, "El lote debe traer entre 1 y 500 muestras")
    try:
        return servicio_flujo.ingresar_lote(conn, datos.tripulante_id, [(m.indicador, m.valor) for m in datos.muestras])
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.post("/flujo/vaciar")
def vaciar_flujo(datos: VaciarIn, conn=Depends(conexion), _: dict = Depends(requiere("clinico:escribir"))) -> dict:
    """Cierra ya las ventanas abiertas y registra su resumen (útil al desconectar un dispositivo)"""
    if datos.tripulante_id:
        requerir_tripulante(conn, datos.tripulante_id)
    return servicio_flujo.vaciar(conn, datos.tripulante_id)
