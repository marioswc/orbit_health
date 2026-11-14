from fastapi import APIRouter

from . import auth, bienestar, enlace, lecturas, sistema

router = APIRouter()
for modulo in (sistema, auth, lecturas, bienestar, enlace):
    router.include_router(modulo.router)
