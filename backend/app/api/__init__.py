from fastapi import APIRouter

from . import auth, bienestar, enlace, informe, lecturas, sistema

router = APIRouter()
for modulo in (sistema, auth, lecturas, bienestar, enlace, informe):
    router.include_router(modulo.router)
