from fastapi import APIRouter

from . import auth, bienestar, enlace, informe, lecturas, sensores, sistema

router = APIRouter()
for modulo in (sistema, auth, lecturas, bienestar, enlace, informe, sensores):
    router.include_router(modulo.router)
