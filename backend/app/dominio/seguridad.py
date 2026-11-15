"""Seguridad local sin dependencias externas (a bordo no hay internet ni proveedor de identidad).

Diseño pensado para el entorno:
- PIN numérico (se teclea con guantes o en pantalla táctil) con PBKDF2 y sal propia por tripulante.
- Los bloqueos por intentos fallidos son temporales: un bloqueo permanente podría impedir atender una emergencia.
- Lo clínico lo puede ver y registrar cualquier tripulante autenticado (un compañero puede quedar incapacitado).
  El diario y el PHQ-2 son exclusivos de su dueño.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta

ROLES = ("tripulante", "comandante")      # todos son astronautas; no hay médico a bordo, solo un comandante con permisos extra
_PIN = re.compile(r"^\d{6,10}$")

# Acción -> roles autorizados. "autenticado" significa cualquier tripulante con sesión.
PERMISOS = {
    "clinico:leer": set(ROLES),
    "clinico:escribir": set(ROLES),
    "enlace:cambiar": {"comandante"},
    "pin:reiniciar": {"comandante"},
    "auditoria:leer": {"comandante"},
    "demo:ejecutar": {"comandante"},
    "salud_mental:avisos": {"comandante"},
}


def pin_valido(pin: str) -> bool:
    return bool(_PIN.match(pin or ""))


def generar_pin(largo: int = 6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(largo))


def generar_codigo_recuperacion() -> str:
    t = secrets.token_hex(6).upper()
    return "-".join(t[i:i + 4] for i in range(0, 12, 4))


def hash_secreto(valor: str, iteraciones: int, sal_hex: str | None = None) -> tuple[str, str]:
    sal = bytes.fromhex(sal_hex) if sal_hex else secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", valor.encode("utf-8"), sal, iteraciones)
    return sal.hex(), h.hex()


def verificar_secreto(valor: str, sal_hex: str, hash_hex: str, iteraciones: int) -> bool:
    _, h = hash_secreto(valor, iteraciones, sal_hex)
    return hmac.compare_digest(h, hash_hex)


def nuevo_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def tras_fallo(intentos_previos: int, ahora: datetime, max_intentos: int, bloqueo_min: float) -> tuple[int, str | None]:
    """Devuelve (intentos, bloqueado_hasta). Al llegar al máximo se bloquea un tiempo limitado y se reinicia la cuenta."""
    intentos = intentos_previos + 1
    if intentos >= max_intentos:
        return 0, (ahora + timedelta(minutes=bloqueo_min)).isoformat()
    return intentos, None


def esta_bloqueado(bloqueado_hasta: str | None, ahora: datetime) -> bool:
    return bool(bloqueado_hasta and bloqueado_hasta > ahora.isoformat())


def permitido(rol: str, accion: str) -> bool:
    return rol in PERMISOS.get(accion, set())
