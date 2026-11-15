import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import config
from .api import router
from .fuentes.semilla import sembrar
from .repositorios.conexion import get_conn, init_db
from .servicios import recuperacion

log = logging.getLogger("orbit")


async def _respaldos_periodicos() -> None:
    while True:
        await asyncio.sleep(config.RESPALDO_CADA_MIN * 60)
        try:
            await asyncio.to_thread(recuperacion.hacer_respaldo)
        except Exception:                                  # un fallo de respaldo no debe tumbar el servicio
            log.exception("Falló el respaldo automático")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arranque = recuperacion.arranque_seguro()
    if app.state.arranque["estado"] != "sana" and app.state.arranque["estado"] != "nueva":
        log.warning("Autorrecuperación: %s", app.state.arranque["detalle"])
    init_db()
    if config.SEED_DEMO:
        conn = get_conn()
        try:
            sembrar(conn)
        finally:
            conn.close()
    if config.PRECALENTAR:                                 # en segundo plano: el arranque no espera al modelo
        from .servicios import explicador_local, voz_local
        asyncio.get_running_loop().run_in_executor(None, explicador_local.precalentar_modelo)
        asyncio.get_running_loop().run_in_executor(None, voz_local.precalentar_stt)
    tarea = None
    if config.RESPALDO_CADA_MIN > 0:
        try:
            recuperacion.hacer_respaldo()                  # un respaldo bueno desde el primer minuto
        except Exception:
            log.exception("Falló el respaldo inicial")
        tarea = asyncio.create_task(_respaldos_periodicos())
    yield
    from .servicios.simulacion_viva import SIMULACION
    await SIMULACION.detener()
    if tarea:
        tarea.cancel()


app = FastAPI(title="ORBIT Health", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def cabeceras_de_seguridad(request, call_next):
    """Cabeceras básicas en toda respuesta. Sin CSP estricta: index.html lleva un script en línea (tema claro/oscuro)."""
    r = await call_next(request)
    r.headers.setdefault("X-Content-Type-Options", "nosniff")
    r.headers.setdefault("X-Frame-Options", "DENY")
    r.headers.setdefault("Referrer-Policy", "no-referrer")
    r.headers.setdefault("Permissions-Policy", "camera=(), geolocation=(), microphone=(self)")
    r.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    ruta = request.url.path
    if ruta.startswith("/api"):
        r.headers.setdefault("Cache-Control", "no-store")             # nada clínico se guarda en cachés del navegador
    elif ruta.startswith("/assets/"):
        r.headers.setdefault("Cache-Control", "public, max-age=31536000, immutable")   # nombres con hash: nunca cambian
    elif r.status_code == 200:
        r.headers["Cache-Control"] = "no-cache"                        # página, service worker y manifiesto: siempre revalidar,
    return r                                                           # así una versión nueva se detecta al abrir la app


app.include_router(router)
if config.DEMO_API:
    from .api import demo

    app.include_router(demo.router)


def _montar_frontend() -> None:
    ruta = Path(config.FRONTEND_DIST) if config.FRONTEND_DIST else config.RAIZ / "frontend" / "dist"
    if ruta.is_dir():
        app.mount("/", StaticFiles(directory=ruta, html=True), name="frontend")


_montar_frontend()
