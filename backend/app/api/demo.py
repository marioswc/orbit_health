from fastapi import APIRouter, Depends, HTTPException

from .. import config
from ..dominio import acciones, comparativa, reglas
from ..dominio import enlace as modelo_enlace
from ..fuentes import dispositivo_simulado, escenarios
from ..servicios import estado as servicio_estado
from ..servicios.simulacion_viva import GUIONES, SIMULACION
from ..servicios import lecturas as servicio_lecturas
from .dependencias import requerir_tripulante
from .dependencias import conexion, requiere

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/escenarios")
def listar(_: dict = Depends(requiere("demo:ejecutar"))) -> list[dict]:
    """Lista de escenarios de demostración disponibles"""
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
                                   artefactos: bool = False,
                                   conn=Depends(conexion), _: dict = Depends(requiere("demo:ejecutar"))) -> dict:
    """Un dispositivo portátil simulado envía `ticks` rondas de constantes vitales (origen 'sensor'). Escribe datos de demo."""
    requerir_tripulante(conn, tid)
    try:
        serie = dispositivo_simulado.generar(perfil, ticks, semilla, artefactos=artefactos)
    except ValueError as e:
        raise HTTPException(422, str(e))
    rondas, primero = [], {"amarillo": None, "rojo": None}
    for i, tick in enumerate(serie, start=1):
        for indicador, valor in tick.items():
            servicio_lecturas.registrar_lectura(conn, tid, indicador, valor, origen="simulado")
        # El nivel de una ronda incluye señales fisiológicas y ambientales, no solo la última lectura.
        e = servicio_estado.estado_tripulante(conn, tid)
        nivel = e["nivel_general"]
        rondas.append({"ronda": i, "valores": tick, "nivel": nivel, "puntos_news2": e["news2"]["puntos"]})
        for objetivo in ("amarillo", "rojo"):
            if primero[objetivo] is None and nivel == objetivo:
                primero[objetivo] = i
    return {"perfil": perfil, "semilla": semilla, "rondas": rondas,
            "primera_ronda_amarillo": primero["amarillo"], "primera_ronda_rojo": primero["rojo"]}


@router.post("/simulacion/iniciar")
async def iniciar_simulacion(guion: str = "mision_en_vivo", ritmo: int = 15, tick_s: float = 1.0, semilla: int = 7,
                             _: dict = Depends(requiere("demo:ejecutar"))) -> dict:
    """Pone en marcha una misión simulada en vivo: las bandas envían solas, el enlace se corta y vuelve. Escribe datos de demo"""
    if not 1 <= ritmo <= 3600:
        raise HTTPException(422, "ritmo debe estar entre 1 y 3600 segundos de misión por tick")
    if not 0.01 <= tick_s <= 10:
        raise HTTPException(422, "tick_s debe estar entre 0.01 y 10 segundos")
    try:
        return await SIMULACION.iniciar(ritmo, tick_s, semilla, guion)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except RuntimeError as e:
        raise HTTPException(409, str(e))


@router.post("/simulacion/detener")
async def detener_simulacion(_: dict = Depends(requiere("demo:ejecutar"))) -> dict:
    """Detiene la misión simulada, cierra las ventanas abiertas y devuelve el enlace a la normalidad"""
    return await SIMULACION.detener()


@router.get("/simulacion/estado")
def estado_simulacion(_: dict = Depends(requiere("demo:ejecutar"))) -> dict:
    """Progreso de la misión simulada: minuto, línea de tiempo narrada y hitos (primer rojo, alerta colectiva, retenidos)"""
    return {**SIMULACION.estado(), "guiones_disponibles": GUIONES}
