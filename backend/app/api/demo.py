from fastapi import APIRouter, Depends, HTTPException

from .. import config
from ..dominio import acciones, comparativa, reglas
from ..dominio import enlace as modelo_enlace
from ..fuentes import dispositivo_simulado, escenarios
from ..servicios import estado as servicio_estado
from ..servicios import lecturas as servicio_lecturas
from .dependencias import requerir_tripulante
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


@router.post("/sensor/{tid}")
def dispositivo_simulado_en_marcha(tid: str, perfil: str = "deterioro_respiratorio", ticks: int = 12, semilla: int | None = 7,
                                   conn=Depends(conexion), _: dict = Depends(requiere("demo:ejecutar"))) -> dict:
    """Un dispositivo portátil simulado envía `ticks` rondas de constantes vitales (origen 'sensor'). Escribe datos de demo."""
    requerir_tripulante(conn, tid)
    try:
        serie = dispositivo_simulado.generar(perfil, ticks, semilla)
    except ValueError as e:
        raise HTTPException(422, str(e))
    rondas, primero = [], {"amarillo": None, "rojo": None}
    for i, tick in enumerate(serie, start=1):
        for indicador, valor in tick.items():
            servicio_lecturas.registrar_lectura(conn, tid, indicador, valor, origen="sensor")
        # El nivel de una ronda es el estado global del tripulante al terminarla, no el de la última lectura.
        e = servicio_estado.estado_tripulante(conn, tid)
        nivel = e["nivel_fisiologico"]
        rondas.append({"ronda": i, "valores": tick, "nivel": nivel, "puntos_news2": e["news2"]["puntos"]})
        for objetivo in ("amarillo", "rojo"):
            if primero[objetivo] is None and nivel == objetivo:
                primero[objetivo] = i
    return {"perfil": perfil, "semilla": semilla, "rondas": rondas,
            "primera_ronda_amarillo": primero["amarillo"], "primera_ronda_rojo": primero["rojo"]}
