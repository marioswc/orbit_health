from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config, queue_manager as qm, servicio
from .db import get_conn, init_db
from .seed import sembrar
from .validacion import INDICADORES

ENLACE = {"activo": True, "entorno": "marte"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if config.SEED_DEMO:
        conn = get_conn()
        try:
            sembrar(conn)
        finally:
            conn.close()
    yield


app = FastAPI(title="ORBIT Health", version="0.1.0", lifespan=lifespan)


def conexion():
    conn = get_conn()
    try:
        yield conn
    finally:
        conn.close()


class LecturaIn(BaseModel):
    tripulante_id: str
    indicador: str
    valor: float


class DiarioIn(BaseModel):
    tripulante_id: str
    titulo: str | None = None
    contenido: str = Field(min_length=1)


class TamizajeIn(BaseModel):
    tripulante_id: str
    item1: int = Field(ge=0, le=3)
    item2: int = Field(ge=0, le=3)


class EnlaceIn(BaseModel):
    activo: bool
    entorno: str = "marte"


def _requerir(conn, tid: str) -> None:
    if not servicio.existe_tripulante(conn, tid):
        raise HTTPException(404, "Tripulante no encontrado")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/indicadores")
def indicadores() -> list[dict]:
    return [{"clave": k, "etiqueta": v[0], "unidad": v[1], "min": v[2], "max": v[3]}
            for k, v in INDICADORES.items()]


@app.get("/api/tripulantes")
def tripulantes(conn=Depends(conexion)) -> list[dict]:
    return [dict(f) for f in conn.execute("SELECT id, nombre, rol FROM tripulantes ORDER BY id")]


@app.post("/api/lecturas")
def crear_lectura(datos: LecturaIn, conn=Depends(conexion)) -> dict:
    _requerir(conn, datos.tripulante_id)
    try:
        return servicio.registrar_lectura(conn, datos.tripulante_id, datos.indicador, datos.valor)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/api/estado/{tid}")
def estado(tid: str, conn=Depends(conexion)) -> dict:
    _requerir(conn, tid)
    return servicio.estado_tripulante(conn, tid)


@app.post("/api/diario")
def crear_diario(nota: DiarioIn, conn=Depends(conexion)) -> dict:
    """Guarda en local. Por diseño no escribe en la cola de salida."""
    _requerir(conn, nota.tripulante_id)
    cur = conn.execute(
        "INSERT INTO diario_privado (tripulante_id, titulo, contenido) VALUES (?,?,?)",
        (nota.tripulante_id, nota.titulo, nota.contenido))
    conn.commit()
    return {"diario_id": cur.lastrowid, "privado": True, "transmitido_tierra": False}


@app.get("/api/diario/{tid}")
def listar_diario(tid: str, conn=Depends(conexion)) -> list[dict]:
    _requerir(conn, tid)
    return [dict(f) for f in conn.execute(
        "SELECT id, titulo, contenido, ts FROM diario_privado WHERE tripulante_id=? ORDER BY id DESC LIMIT 50",
        (tid,))]


@app.post("/api/tamizajes")
def crear_tamizaje(datos: TamizajeIn, conn=Depends(conexion)) -> dict:
    _requerir(conn, datos.tripulante_id)
    return servicio.registrar_tamizaje(conn, datos.tripulante_id, datos.item1, datos.item2)


@app.get("/api/enlace")
def ver_enlace() -> dict:
    return ENLACE


@app.post("/api/enlace")
def cambiar_enlace(datos: EnlaceIn, conn=Depends(conexion)) -> dict:
    if datos.entorno.lower() not in ("marte", "luna"):
        raise HTTPException(422, "entorno debe ser 'marte' o 'luna'")
    ENLACE.update(activo=datos.activo, entorno=datos.entorno.lower())
    despachados = qm.despachar(conn, ENLACE["activo"], ENLACE["entorno"])
    return {**ENLACE, "despachados": despachados}


@app.get("/api/cola")
def cola(conn=Depends(conexion)) -> dict:
    qm.actualizar_recibidos(conn)
    items = qm.listar(conn)
    resumen: dict = {}
    for i in items:
        resumen.setdefault(i["estado"], {1: 0, 2: 0, 3: 0})[i["prioridad"]] += 1
    return {"enlace": ENLACE, "resumen": resumen, "items": items}


@app.get("/api/cola/verificar")
def verificar(conn=Depends(conexion)) -> dict:
    return qm.verificar_cadena(conn)


def _montar_frontend() -> None:
    ruta = Path(config.FRONTEND_DIST) if config.FRONTEND_DIST else Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if ruta.is_dir():
        app.mount("/", StaticFiles(directory=ruta, html=True), name="frontend")


_montar_frontend()
