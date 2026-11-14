from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import config
from .api import router
from .fuentes.semilla import sembrar
from .repositorios.conexion import get_conn, init_db


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
app.include_router(router)


def _montar_frontend() -> None:
    ruta = Path(config.FRONTEND_DIST) if config.FRONTEND_DIST else config.RAIZ / "frontend" / "dist"
    if ruta.is_dir():
        app.mount("/", StaticFiles(directory=ruta, html=True), name="frontend")


_montar_frontend()
