from fastapi import APIRouter

from . import asistente, auth, bienestar, enlace, informe, lecturas, sensores, sistema, voz

router = APIRouter()
for modulo in (sistema, auth, lecturas, bienestar, enlace, informe, sensores, asistente, voz):
    router.include_router(modulo.router)
