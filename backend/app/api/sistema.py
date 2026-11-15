from fastapi import APIRouter, Depends, HTTPException, Request

from ..dominio.catalogos import INDICADORES
from ..dominio import peligros as dominio_peligros
from ..dominio.entornos import DATOS as ENTORNOS
from ..dominio.explicaciones import DATOS as EXPLICACIONES
from ..dominio.umbrales import UMBRALES
from ..repositorios import tripulantes
from ..servicios import diagnostico, recuperacion
from .dependencias import conexion, requiere

router = APIRouter(prefix="/api", tags=["sistema"])


@router.get("/sistema/diagnostico")
def diagnostico_del_sistema(_: dict = Depends(requiere("auditoria:leer"))) -> dict:
    """Configuración efectiva (con su origen), estado de la voz y la IA, y advertencias de despliegue. Solo el comandante con login activo; sin secretos"""
    return diagnostico.reunir()


@router.get("/health")
def health() -> dict:
    """Comprobación de que el servidor responde"""
    return {"status": "ok"}


@router.get("/salud")
def salud(request: Request) -> dict:
    """Estado de la base y de los respaldos. Pensado para que un tripulante no técnico sepa si todo está bien."""
    return recuperacion.estado_salud(arranque=getattr(request.app.state, "arranque", None))


@router.get("/umbrales")
def umbrales_estado() -> dict:
    """Perfil, versión y estado de validación clínica de los umbrales en uso."""
    return {
        "version": UMBRALES["version"],
        "estado": UMBRALES["estado"],
        "perfil": UMBRALES["perfil"],
        "semaforo": UMBRALES["semaforo"],
        "linea_base": {
            "dias": UMBRALES["linea_base"]["dias"],
            "min_muestras": UMBRALES["linea_base"]["min_muestras"],
            "metodo": UMBRALES["linea_base"]["metodo"],
            "desviaciones": UMBRALES["linea_base"]["desviaciones"],
        },
    }


@router.get("/indicadores")
def indicadores() -> list[dict]:
    """Catálogo de indicadores con su unidad y rango de captura"""
    return [{"clave": k, "etiqueta": v[0], "unidad": v[1], "min": v[2], "max": v[3]}
            for k, v in INDICADORES.items()]


@router.get("/explicaciones")
def explicaciones() -> dict:
    """Qué es cada medición, por qué se mide, cómo medirla y qué cambia en el espacio."""
    return EXPLICACIONES


@router.get("/explicaciones/{clave}")
def explicacion(clave: str) -> dict:
    """Explicación de un indicador: qué es, por qué se mide y cómo medirlo"""
    if clave not in EXPLICACIONES["explicaciones"]:
        raise HTTPException(404, "No hay explicación para ese indicador")
    return {"clave": clave, "estado": EXPLICACIONES["estado"], "aviso": EXPLICACIONES["aviso"],
            **EXPLICACIONES["explicaciones"][clave]}


@router.get("/entornos")
def entornos() -> dict:
    """Entornos de la misión con su gravedad y si la estimación de pérdida ósea aplica en cada uno"""
    return ENTORNOS


@router.get("/entornos/{clave}")
def entorno(clave: str) -> dict:
    """Un entorno de la misión: gravedad y aplicabilidad de la estimación ósea"""
    if clave not in ENTORNOS["entornos"]:
        raise HTTPException(404, "Entorno desconocido")
    return {"clave": clave, "nota_general": ENTORNOS["nota_general"], "fuente_gravedad": ENTORNOS["fuente_gravedad"],
            **ENTORNOS["entornos"][clave]}


@router.get("/peligros")
def peligros() -> dict:
    """Marco de peligros y riesgos del HRP, con la cobertura real de ORBIT Health por cada riesgo."""
    return {**dominio_peligros.DATOS, "resumen_cobertura": dominio_peligros.resumen_cobertura()}


@router.get("/tripulantes")
def listar_tripulantes(conn=Depends(conexion)) -> list[dict]:
    """Lista de tripulantes (id, nombre y rol) para el selector de acceso"""
    return tripulantes.listar(conn)
