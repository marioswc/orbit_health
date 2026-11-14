from fastapi import APIRouter

from . import bienestar, enlace, lecturas, sistema

router = APIRouter()
for modulo in (sistema, lecturas, bienestar, enlace):
    router.include_router(modulo.router)
