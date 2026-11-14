"""Motor de la misión simulada en vivo: bandas que "envían" solas, enlace que se corta y vuelve, y una historia que contar.

Usa EXACTAMENTE el mismo canal que una banda real (el flujo continuo de sensores), así que lo que se ve en la demo es el
sistema de verdad trabajando, no datos pintados. Solo los valores son inventados.

El reloj de la misión va más rápido que el real (`ritmo` segundos simulados por tick). Para no depender del reloj de pared
en las ventanas del flujo, se le pasa la hora simulada; al terminar o detenerse se limpia su estado en memoria para que una
hora simulada "del futuro" no deje bloqueados los extremos de un uso normal posterior.
"""
from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timedelta, timezone

from ..fuentes import guion_vivo as guion
from ..repositorios import cola as repo_cola
from ..repositorios.conexion import get_conn
from . import alertas, cola, estado, flujo, lecturas

GUIONES = {"mision_en_vivo": "Misión de 34 min simulados: sube el CO₂, la tripulación empeora, se pierde el enlace y vuelve"}


class SimulacionViva:
    def __init__(self) -> None:
        self._tarea: asyncio.Task | None = None
        self._cerrojo = threading.Lock()
        self._estado = self._estado_inicial()

    # ---------- estado visible ----------
    @staticmethod
    def _estado_inicial() -> dict:
        return {"activa": False, "finalizada": False, "guion": None, "ritmo": None, "tick_s": None, "tick": 0,
                "minuto_mision": 0.0, "duracion_min": guion.DURACION_MIN, "progreso_pct": 0.0,
                "eventos": [], "hitos": {}, "error": None, "aviso": None, "inicio_ts": None, "fin_ts": None}

    def estado(self) -> dict:
        with self._cerrojo:
            e = dict(self._estado)
            e["eventos"] = [dict(x) for x in self._estado["eventos"]]
            e["hitos"] = dict(self._estado["hitos"])
            return e

    @property
    def activa(self) -> bool:
        return bool(self._tarea and not self._tarea.done())

    # ---------- control ----------
    async def iniciar(self, ritmo: int = 15, tick_s: float = 1.0, semilla: int = 7, guion_id: str = "mision_en_vivo") -> dict:
        if guion_id not in GUIONES:
            raise ValueError(f"guion debe ser uno de: {', '.join(GUIONES)}")
        if self.activa:
            raise RuntimeError("Ya hay una simulación en marcha")
        flujo.reiniciar()
        from .. import config
        aviso = None
        if ritmo > config.FLUJO_VENTANA_S > 0:
            aviso = (f"Con ritmo={ritmo} s por tick, mayor que la ventana de sensores ({config.FLUJO_VENTANA_S:g} s), "
                     "solo se registra una de cada dos rondas y los picos pueden perderse. Usa un ritmo menor o igual a la ventana.")
        with self._cerrojo:
            self._estado = {**self._estado_inicial(), "activa": True, "guion": guion_id, "ritmo": ritmo, "tick_s": tick_s,
                            "inicio_ts": datetime.now(timezone.utc).isoformat(), "aviso": aviso,
                            "eventos": [{"t_min": t, "texto": txt, "ocurrido": False} for t, txt in guion.NARRACION]}
        self._tarea = asyncio.create_task(self._bucle(ritmo, tick_s, semilla))
        return self.estado()

    async def detener(self) -> dict:
        if self._tarea and not self._tarea.done():
            self._tarea.cancel()
            try:
                await self._tarea
            except asyncio.CancelledError:
                pass
        return self.estado()

    # ---------- motor ----------
    async def _bucle(self, ritmo: int, tick_s: float, semilla: int) -> None:
        t0 = datetime.now(timezone.utc)
        try:
            tick = 0
            while True:
                terminado = await asyncio.to_thread(self._paso, tick, ritmo, semilla, t0)
                if terminado:
                    break
                tick += 1
                await asyncio.sleep(tick_s)
        except asyncio.CancelledError:
            raise
        except Exception as e:                                   # una falla no debe tumbar el servidor
            with self._cerrojo:
                self._estado["error"] = f"{type(e).__name__}: {e}"
        finally:
            await asyncio.shield(asyncio.to_thread(self._cierre))

    def _paso(self, tick: int, ritmo: int, semilla: int, t0: datetime) -> bool:
        minuto = tick * ritmo / 60
        previo = (tick - 1) * ritmo / 60 if tick > 0 else -1.0
        t_sim = t0 + timedelta(minutes=minuto)
        conn = get_conn()
        try:
            if tick == 0:
                cola.cambiar_enlace(conn, True, guion.ENTORNO_INICIAL)
                for tid, horas in guion.SUENO_INICIAL.items():           # el resumen de sueño que entrega la banda
                    lecturas.registrar_lectura(conn, tid, "sueno_horas", horas, origen="simulado")
            for _, activo, _ in guion.eventos_enlace_entre(previo, minuto):
                if tick > 0 or not activo:
                    cola.cambiar_enlace(conn, activo, guion.ENTORNO_INICIAL)
            for tid, indicador, valor in guion.muestras_en(minuto, tick, semilla):
                flujo.ingresar(conn, tid, indicador, valor, ahora=t_sim, origen="simulado")
            terminado = minuto >= guion.DURACION_MIN
            if terminado:
                for tid, minutos in guion.EJERCICIO_FINAL.items():
                    lecturas.registrar_lectura(conn, tid, "ejercicio_min", minutos, origen="simulado")
            self._registrar_hitos(conn, tick, minuto, terminado)
            return terminado
        finally:
            conn.close()

    def _registrar_hitos(self, conn, tick: int, minuto: float, terminado: bool) -> None:
        niveles = {tid: estado.estado_tripulante(conn, tid)["nivel_fisiologico"] for tid in guion.TRIPULANTES}
        colectiva = alertas.alertas_colectivas(conn)["alertas"]
        retenidos = repo_cola.retenidos(conn)
        with self._cerrojo:
            e = self._estado
            e["tick"], e["minuto_mision"] = tick, round(minuto, 2)
            e["progreso_pct"] = round(min(100.0, minuto / guion.DURACION_MIN * 100), 1)
            for ev in e["eventos"]:
                if minuto >= ev["t_min"]:
                    ev["ocurrido"] = True
            h = e["hitos"]
            h["niveles"] = niveles
            for tid, nivel in niveles.items():
                if nivel == "rojo":
                    h.setdefault("primer_rojo", {"tripulante": tid, "minuto": round(minuto, 2)})
            if colectiva:
                h.setdefault("alerta_colectiva", {"minuto": round(minuto, 2), "afectados": colectiva[0]["afectados"]})
            h["max_retenidos_a_bordo"] = max(h.get("max_retenidos_a_bordo", 0), retenidos)
            if terminado:
                e["finalizada"] = True

    def _cierre(self) -> None:
        """Cierra ventanas abiertas, devuelve el enlace a la normalidad y limpia el reloj simulado en memoria."""
        conn = get_conn()
        try:
            flujo.vaciar(conn)
            if not repo_enlace_activo(conn):
                cola.cambiar_enlace(conn, True, guion.ENTORNO_INICIAL)
        finally:
            conn.close()
            flujo.reiniciar()
            with self._cerrojo:
                self._estado["activa"] = False
                self._estado["fin_ts"] = datetime.now(timezone.utc).isoformat()


def repo_enlace_activo(conn) -> bool:
    from ..repositorios import enlace as repo_enlace
    return repo_enlace.leer(conn)["activo"]


SIMULACION = SimulacionViva()
