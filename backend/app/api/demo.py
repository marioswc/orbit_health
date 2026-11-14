from fastapi import APIRouter, Depends, HTTPException

from .. import config
from ..dominio import acciones, comparativa, reglas
from ..dominio import enlace as modelo_enlace
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


@router.get("/comparativa")
def comparativa_con_y_sin_orbit(entorno: str = "marte", respuesta_tierra_min: float = 1.0,
                                _: dict = Depends(requiere("clinico:leer"))) -> dict:
    """Mismo evento (hipoxia severa) visto con y sin ORBIT. No escribe datos; es una ilustración con supuestos."""
    try:
        retardo = modelo_enlace.retardo_base_s(entorno)
    except KeyError:
        raise HTTPException(422, f"entorno debe ser uno de: {', '.join(modelo_enlace.entornos())}")
    if respuesta_tierra_min < 0:
        raise HTTPException(422, "respuesta_tierra_min no puede ser negativo")
    r = reglas.evaluar_news2({"spo2": 88})
    pasos = acciones.acciones_sugeridas(r.nivel, reglas.captura_recomendada_min(r.nivel))
    out = comparativa.linea_de_tiempo(retardo, respuesta_tierra_min * 60, r.nivel, pasos, config.FACTOR_ACELERACION)
    return {"entorno": entorno, "retardo_unidireccional_s": retardo, "respuesta_tierra_min": respuesta_tierra_min,
            "evento": "SpO₂ 88 %", **out}
