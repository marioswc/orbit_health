"""Casos de uso de autenticación local. Sin internet: no hay correo ni proveedor de identidad."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio import seguridad as seg
from ..repositorios import seguridad as repo
from ..repositorios import tripulantes
from . import auditoria


class AuthError(Exception):
    """codigo: credenciales | bloqueado | sesion | permiso"""

    def __init__(self, codigo: str, mensaje: str = "", hasta: str | None = None):
        super().__init__(mensaje or codigo)
        self.codigo, self.hasta = codigo, hasta


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def inscribir(conn: sqlite3.Connection, tid: str, rol: str, pin: str | None = None,
              ahora: datetime | None = None) -> dict:
    """Alta de credenciales. Devuelve el PIN (solo si se generó) y el código de recuperación, una única vez."""
    ahora = ahora or _ahora()
    if not tripulantes.existe(conn, tid):
        raise ValueError("Tripulante inexistente")
    if rol not in seg.ROLES:
        raise ValueError(f"Rol inválido: {rol}")
    if repo.obtener_credencial(conn, tid):
        raise ValueError("El tripulante ya tiene credenciales; usa el reinicio de PIN")
    if rol == "comandante" and repo.hay_comandante(conn):
        raise ValueError("Ya hay un comandante en la tripulación: solo puede haber uno")
    generado = pin is None
    pin = pin or seg.generar_pin()
    if not seg.pin_valido(pin):
        raise ValueError("El PIN debe tener entre 6 y 10 dígitos")
    codigo = seg.generar_codigo_recuperacion()
    ps, ph = seg.hash_secreto(pin, config.PBKDF2_ITER)
    rs, rh = seg.hash_secreto(codigo, config.PBKDF2_ITER)
    repo.insertar_credencial(conn, tid, rol, ps, ph, rs, rh, ahora.isoformat())
    auditoria.registrar(conn, "sistema", "inscripcion", tid, {"rol": rol})
    conn.commit()
    return {"tripulante_id": tid, "rol": rol, "codigo_recuperacion": codigo, **({"pin": pin} if generado else {})}


def _fallo(conn, tid: str, cred: dict, ahora: datetime, accion: str) -> None:
    intentos, hasta = seg.tras_fallo(cred["intentos_fallidos"], ahora, config.MAX_INTENTOS, config.BLOQUEO_MIN)
    repo.guardar_intentos(conn, tid, intentos, hasta)
    auditoria.registrar(conn, tid, accion, tid)
    if hasta:
        auditoria.registrar(conn, "sistema", "bloqueo_temporal", tid, {"hasta": hasta})
    conn.commit()


def login(conn: sqlite3.Connection, tid: str, pin: str, ahora: datetime | None = None) -> dict:
    ahora = ahora or _ahora()
    cred = repo.obtener_credencial(conn, tid)
    if cred is None:
        seg.hash_secreto(pin or "", config.PBKDF2_ITER)       # tiempo similar al de un usuario real
        raise AuthError("credenciales", "Tripulante o PIN incorrectos")
    if seg.esta_bloqueado(cred["bloqueado_hasta"], ahora):
        raise AuthError("bloqueado", "Acceso bloqueado temporalmente", cred["bloqueado_hasta"])
    if not seg.verificar_secreto(pin or "", cred["pin_salt"], cred["pin_hash"], config.PBKDF2_ITER):
        _fallo(conn, tid, cred, ahora, "login_fallido")
        raise AuthError("credenciales", "Tripulante o PIN incorrectos")
    repo.guardar_intentos(conn, tid, 0, None)
    token = seg.nuevo_token()
    expira = ahora + timedelta(hours=config.SESION_HORAS)
    repo.insertar_sesion(conn, seg.hash_token(token), tid, ahora.isoformat(), expira.isoformat())
    auditoria.registrar(conn, tid, "login", tid)
    conn.commit()
    return {"token": token, "expira_ts": expira.isoformat(), "tripulante_id": tid, "rol": cred["rol"]}


def sesion(conn: sqlite3.Connection, token: str | None, ahora: datetime | None = None) -> dict | None:
    if not token:
        return None
    s = repo.obtener_sesion(conn, seg.hash_token(token))
    if not s or s["revocada"] or s["expira_ts"] <= (ahora or _ahora()).isoformat():
        return None
    return {"tripulante_id": s["tripulante_id"], "rol": s["rol"]}


def logout(conn: sqlite3.Connection, token: str, actor: str | None = None) -> None:
    repo.revocar_sesion(conn, seg.hash_token(token))
    auditoria.registrar(conn, actor, "logout", actor)
    conn.commit()


def recuperar(conn: sqlite3.Connection, tid: str, codigo: str, pin_nuevo: str,
              ahora: datetime | None = None) -> dict:
    """Restablece el PIN con el código de recuperación entregado al inscribirse. Comparte el límite de intentos."""
    ahora = ahora or _ahora()
    if not seg.pin_valido(pin_nuevo):
        raise ValueError("El PIN debe tener entre 6 y 10 dígitos")
    cred = repo.obtener_credencial(conn, tid)
    if cred is None:
        raise AuthError("credenciales", "Datos de recuperación incorrectos")
    if seg.esta_bloqueado(cred["bloqueado_hasta"], ahora):
        raise AuthError("bloqueado", "Acceso bloqueado temporalmente", cred["bloqueado_hasta"])
    if not seg.verificar_secreto((codigo or "").upper(), cred["recup_salt"], cred["recup_hash"], config.PBKDF2_ITER):
        _fallo(conn, tid, cred, ahora, "recuperacion_fallida")
        raise AuthError("credenciales", "Datos de recuperación incorrectos")
    nuevo_codigo = seg.generar_codigo_recuperacion()
    ps, ph = seg.hash_secreto(pin_nuevo, config.PBKDF2_ITER)
    rs, rh = seg.hash_secreto(nuevo_codigo, config.PBKDF2_ITER)
    repo.cambiar_pin(conn, tid, ps, ph, ahora.isoformat(), rs, rh)
    repo.revocar_sesiones_de(conn, tid)
    auditoria.registrar(conn, tid, "recuperacion", tid)
    conn.commit()
    return {"codigo_recuperacion": nuevo_codigo}


def reiniciar_pin(conn: sqlite3.Connection, actor: dict, tid: str, ahora: datetime | None = None) -> dict:
    """El comandante reinicia el PIN de otro tripulante (queda auditado). Devuelve un PIN temporal."""
    if not seg.permitido(actor["rol"], "pin:reiniciar"):
        raise AuthError("permiso", "Solo el comandante puede reiniciar un PIN")
    if repo.obtener_credencial(conn, tid) is None:
        raise ValueError("Tripulante sin credenciales")
    pin = seg.generar_pin()
    ps, ph = seg.hash_secreto(pin, config.PBKDF2_ITER)
    repo.cambiar_pin(conn, tid, ps, ph, (ahora or _ahora()).isoformat())
    repo.revocar_sesiones_de(conn, tid)
    auditoria.registrar(conn, actor["tripulante_id"], "reinicio_pin", tid)
    conn.commit()
    return {"tripulante_id": tid, "pin_temporal": pin}
