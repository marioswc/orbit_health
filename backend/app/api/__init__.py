from fastapi import APIRouter

from . import asistente, auth, bienestar, enlace, informe, lecturas, perfil_ia, sensores, sistema, voz

router = APIRouter()
for modulo in (sistema, auth, lecturas, bienestar, enlace, informe, sensores, asistente, voz, perfil_ia):
    router.include_router(modulo.router)
