"""Casos de uso de bienestar: diario, PHQ-2, protocolo de crisis psicológica (con variable de calidad de oxígeno)
y aviso con consentimiento al médico de a bordo.

Por diseño nada de esto se encola hacia Tierra (`cola_salida`).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio import crisis as modelo_crisis
from ..dominio import reglas
from ..repositorios import bienestar as repo
from ..repositorios import lecturas as repo_lecturas
from . import auditoria, preferencias

CORTE_PHQ2 = modelo_crisis.CORTE_PHQ2


def _oxigeno_vigente(conn: sqlite3.Connection, explicito: float | None = None) -> float | None:
    """Usa el valor de O2 indicado o, si no se pasó, la lectura reciente de `o2_cabina` en la ventana activa."""
    if explicito is not None:
        return explicito
    ventana = (datetime.now(timezone.utc) - timedelta(minutes=config.VENTANA_NEWS2_MIN)).isoformat()
    return repo_lecturas.ultimo_global(conn, "o2_cabina", ventana)


def registrar_nota(conn: sqlite3.Connection, tid: str, titulo: str | None, contenido: str) -> dict:
    nota_id = repo.insertar_nota(conn, tid, titulo, contenido)
    conn.commit()
    return {"diario_id": nota_id, "privado": True, "transmitido_tierra": False}


def listar_notas(conn: sqlite3.Connection, tid: str) -> list[dict]:
    return repo.listar_notas(conn, tid)


def registrar_tamizaje(conn: sqlite3.Connection, tid: str, item1: int, item2: int,
                       riesgo_autolesion: bool = False, compartir_medico: bool = False,
                       mensaje_medico: str | None = None,
                       calidad_oxigeno: float | None = None) -> dict:
    o2_efectivo = _oxigeno_vigente(conn, calidad_oxigeno)
    ev = modelo_crisis.evaluar_tamizaje(item1, item2, riesgo_autolesion, o2_efectivo)
    if compartir_medico and not ev["positivo"]:
        raise ValueError("Solo se comparte con el médico un resultado positivo o en crisis")

    tamizaje_id = repo.insertar_tamizaje(
        conn, tid, item1, item2, ev["total"], ev["riesgo_autolesion"],
        ev["nivel_protocolo"], ev["calidad_oxigeno"]["valor_pct"],
    )
    capsulas: list[dict] = []
    for cat in ev["categorias_capsulas"]:
        capsulas.extend(repo.capsulas_por_categoria(conn, cat))

    tono = preferencias.obtener(conn, tid)["tono"]
    protocolo = modelo_crisis.protocolo_crisis(ev["nivel_protocolo"], tono, o2_efectivo)

    aviso_id: int | None = None
    if compartir_medico and ev["positivo"]:
        ahora = datetime.now(timezone.utc).isoformat()
        tipo = "crisis" if ev["nivel_protocolo"] == "crisis" else "tamizaje_positivo"
        aviso_id = repo.insertar_aviso_medico(
            conn, tid, tipo, ev["nivel_protocolo"], tamizaje_id, (mensaje_medico or "").strip() or None, ahora
        )
        auditoria.registrar(
            conn, tid, "consentimiento_salud_mental", tid,
            {"aviso_id": aviso_id, "tipo": tipo, "nivel_protocolo": ev["nivel_protocolo"]},
        )

    conn.commit()
    return {
        "tamizaje_id": tamizaje_id,
        "total": ev["total"],
        "positivo": ev["positivo"],
        "riesgo_autolesion": ev["riesgo_autolesion"],
        "calidad_oxigeno": ev["calidad_oxigeno"],
        "nivel_protocolo": ev["nivel_protocolo"],
        "protocolo": protocolo,
        "capsulas": capsulas,
        "compartido_medico": aviso_id is not None,
        "aviso_medico_id": aviso_id,
        "transmitido_tierra": False,
    }


def obtener_protocolo(conn: sqlite3.Connection, tid: str | None = None, nivel: str = "crisis",
                      calidad_oxigeno: float | None = None) -> dict:
    """Devuelve el protocolo de crisis o seguimiento adaptado al tono elegido y a la calidad de oxígeno vigente."""
    tono = preferencias.obtener(conn, tid)["tono"] if tid else "directo"
    o2_efectivo = _oxigeno_vigente(conn, calidad_oxigeno)
    proto = modelo_crisis.protocolo_crisis(nivel, tono, o2_efectivo)
    if nivel == "crisis":
        capsulas = repo.capsulas_por_categoria(conn, "crisis")
    elif nivel == "seguimiento":
        capsulas = repo.capsulas_por_categoria(conn, "autorregulacion")
    else:
        capsulas = []
    return {**proto, "capsulas": capsulas}


def solicitar_apoyo_medico(conn: sqlite3.Connection, tid: str, consentimiento: bool,
                           tipo: str = "crisis", tamizaje_id: int | None = None,
                           mensaje: str | None = None) -> dict:
    """Crea un aviso interno al médico de a bordo SOLO con el consentimiento explícito del tripulante."""
    if not consentimiento:
        raise ValueError("Se requiere el consentimiento explícito del tripulante para avisar al médico")
    if tipo not in modelo_crisis.TIPOS_AVISO:
        raise ValueError(f"tipo debe ser uno de: {', '.join(modelo_crisis.TIPOS_AVISO)}")

    nivel = "crisis" if tipo == "crisis" else "seguimiento"
    if tamizaje_id is not None:
        tam = repo.obtener_tamizaje(conn, tamizaje_id)
        if not tam or tam["tripulante_id"] != tid:
            raise LookupError("Tamizaje no encontrado para este tripulante")
        if tipo == "tamizaje_positivo" and tam["total"] < CORTE_PHQ2 and not tam["riesgo_autolesion"] and tam["nivel_protocolo"] == "ninguno":
            raise ValueError("El tamizaje indicado no es positivo")
        if tam["nivel_protocolo"] == "crisis":
            nivel = "crisis"

    ahora = datetime.now(timezone.utc).isoformat()
    aviso_id = repo.insertar_aviso_medico(
        conn, tid, tipo, nivel, tamizaje_id, (mensaje or "").strip() or None, ahora
    )
    auditoria.registrar(
        conn, tid, "consentimiento_salud_mental", tid,
        {"aviso_id": aviso_id, "tipo": tipo, "nivel_protocolo": nivel},
    )
    conn.commit()
    return {**repo.obtener_aviso_medico(conn, aviso_id), "privado": True, "transmitido_tierra": False}


def revocar_apoyo_medico(conn: sqlite3.Connection, tid: str, aviso_id: int) -> dict:
    """El propio tripulante retira su consentimiento: el aviso deja de mostrarse al médico de a bordo."""
    aviso = repo.obtener_aviso_medico(conn, aviso_id)
    if not aviso:
        raise LookupError("Aviso no encontrado")
    if aviso["tripulante_id"] != tid:
        raise PermissionError("Solo el propio tripulante puede revocar su consentimiento")
    ahora = datetime.now(timezone.utc).isoformat()
    repo.actualizar_estado_aviso(conn, aviso_id, "revocado", ahora)
    auditoria.registrar(conn, tid, "revocacion_salud_mental", tid, {"aviso_id": aviso_id})
    conn.commit()
    return {**repo.obtener_aviso_medico(conn, aviso_id), "privado": True, "transmitido_tierra": False}


def listar_mis_avisos(conn: sqlite3.Connection, tid: str) -> list[dict]:
    return repo.listar_avisos_de_tripulante(conn, tid)


def listar_avisos_medico(conn: sqlite3.Connection, solo_pendientes: bool = False) -> list[dict]:
    return repo.listar_avisos_para_medico(conn, solo_pendientes)


def atender_aviso_medico(conn: sqlite3.Connection, aviso_id: int, actor_id: str | None) -> dict:
    aviso = repo.obtener_aviso_medico(conn, aviso_id)
    if not aviso or aviso["estado"] == "revocado":
        raise LookupError("Aviso no encontrado o revocado por el tripulante")
    ahora = datetime.now(timezone.utc).isoformat()
    repo.actualizar_estado_aviso(conn, aviso_id, "atendido", ahora, actor_id)
    auditoria.registrar(
        conn, actor_id or "sistema", "atencion_salud_mental",
        aviso["tripulante_id"], {"aviso_id": aviso_id},
    )
    conn.commit()
    return {**repo.obtener_aviso_medico(conn, aviso_id), "privado": True, "transmitido_tierra": False}


def registrar_animo(conn: sqlite3.Connection, tid: str, valor: int) -> dict:
    """Ánimo diario 1 a 5. Privado: no se encola. Si es bajo o se aleja de lo habitual, ofrece apoyo."""
    ahora = datetime.now(timezone.utc)
    desde = (ahora - timedelta(days=config.DIAS_LINEA_BASE)).isoformat()
    previo = [p["valor"] for p in repo.animo_desde(conn, tid, desde)]
    linea = reglas.desviacion_linea_base(float(valor), previo, solo_baja=True)   # un ánimo mejor que el habitual no es aviso
    repo.insertar_animo(conn, tid, valor, ahora.isoformat())
    conn.commit()
    bajo = reglas.animo_bajo(valor)
    capsulas = repo.capsulas_por_categoria(conn, "autorregulacion") if (bajo or linea["aviso"]) else []
    return {"valor": valor, "bajo": bajo, "aviso_linea_base": linea["aviso"], "capsulas": capsulas,
            "privado": True, "transmitido_tierra": False}


def serie_animo(conn: sqlite3.Connection, tid: str, dias: float = 14) -> dict:
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
    puntos = repo.animo_desde(conn, tid, desde)
    valores = [p["valor"] for p in puntos]
    return {"puntos": puntos, "media": round(sum(valores) / len(valores), 2) if valores else None, "privado": True}
