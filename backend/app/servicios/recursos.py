"""Recursos de la máquina (memoria y núcleos) en Linux, macOS y Windows, sin dependencias.

Para qué: un modelo de IA de ~1 GB en un equipo con poca RAM libre o con mucho swap (memoria en disco) responde 10 o 50 veces más
lento, y usar todos los hilos lógicos en vez de los núcleos físicos sobrecarga el procesador. Esto permite elegir bien por defecto y
decirle a la persona qué pasa, en vez de que el programa «se sienta lento» sin explicación.
"""
from __future__ import annotations

import functools
import os
import platform
import re
import subprocess
from pathlib import Path


def _ejecutar(orden: list[str], espera: float = 8) -> str:
    try:
        return subprocess.run(orden, capture_output=True, text=True, timeout=espera).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def leer_meminfo(texto: str) -> dict[str, int]:
    """Interpreta el contenido de /proc/meminfo (valores en kB)."""
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^(\w+):\s+(\d+)\s*kB", texto, re.M)}


def memoria() -> dict[str, int | None]:
    """Memoria en MB: total, disponible, y swap total y usado (None si no se puede saber en este sistema)."""
    vacio: dict[str, int | None] = {"total_mb": None, "disponible_mb": None, "swap_total_mb": None, "swap_usado_mb": None}
    sistema = platform.system()
    try:
        if sistema == "Linux":
            m = leer_meminfo(Path("/proc/meminfo").read_text())
            return {"total_mb": m["MemTotal"] // 1024, "disponible_mb": m.get("MemAvailable", m.get("MemFree", 0)) // 1024,
                    "swap_total_mb": m.get("SwapTotal", 0) // 1024, "swap_usado_mb": (m.get("SwapTotal", 0) - m.get("SwapFree", 0)) // 1024}
        if sistema == "Darwin":
            total = int(_ejecutar(["sysctl", "-n", "hw.memsize"]).strip() or 0) // (1024 * 1024)
            vm = _ejecutar(["vm_stat"])
            pagina = int(re.search(r"page size of (\d+) bytes", vm).group(1)) if re.search(r"page size of (\d+) bytes", vm) else 16384
            paginas = sum(int(m.group(1)) for k in ("Pages free", "Pages inactive", "Pages speculative")
                          for m in [re.search(rf"{k}:\s+(\d+)", vm)] if m)
            swap = re.search(r"total = ([\d.]+)M\s+used = ([\d.]+)M", _ejecutar(["sysctl", "vm.swapusage"]))
            return {"total_mb": total or None, "disponible_mb": paginas * pagina // (1024 * 1024) or None,
                    "swap_total_mb": int(float(swap.group(1))) if swap else None, "swap_usado_mb": int(float(swap.group(2))) if swap else None}
        if sistema == "Windows":
            import ctypes

            class Estado(ctypes.Structure):
                _fields_ = [("longitud", ctypes.c_ulong), ("carga", ctypes.c_ulong), ("total_fisica", ctypes.c_ulonglong),
                            ("libre_fisica", ctypes.c_ulonglong), ("total_paginacion", ctypes.c_ulonglong),
                            ("libre_paginacion", ctypes.c_ulonglong), ("total_virtual", ctypes.c_ulonglong),
                            ("libre_virtual", ctypes.c_ulonglong), ("libre_extendida", ctypes.c_ulonglong)]
            e = Estado()
            e.longitud = ctypes.sizeof(Estado)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(e))             # type: ignore[attr-defined]
            pag_usada = (e.total_paginacion - e.libre_paginacion) - (e.total_fisica - e.libre_fisica)
            return {"total_mb": e.total_fisica // 2**20, "disponible_mb": e.libre_fisica // 2**20,
                    "swap_total_mb": max(0, (e.total_paginacion - e.total_fisica)) // 2**20, "swap_usado_mb": max(0, pag_usada) // 2**20}
    except (OSError, KeyError, ValueError, AttributeError, TypeError):
        pass
    return vacio


def contar_nucleos_linux(cpuinfo: str) -> int | None:
    """Núcleos FÍSICOS a partir de /proc/cpuinfo (pares únicos «physical id» + «core id»)."""
    pares, fisico = set(), None
    for linea in cpuinfo.splitlines():
        if linea.startswith("physical id"):
            fisico = linea.split(":")[1].strip()
        elif linea.startswith("core id"):
            pares.add((fisico, linea.split(":")[1].strip()))
    return len(pares) or None


@functools.cache
def nucleos_fisicos() -> int:
    """Núcleos físicos (sin contar los hilos extra de hyper-threading/SMT). Si no se puede saber, la mitad de los lógicos en equipos
    de 4 o más hilos, que es lo habitual en portátiles."""
    logicos = os.cpu_count() or 2
    sistema = platform.system()
    n: int | None = None
    try:
        if sistema == "Linux":
            n = contar_nucleos_linux(Path("/proc/cpuinfo").read_text())
        elif sistema == "Darwin":
            n = int(_ejecutar(["sysctl", "-n", "hw.physicalcpu"]).strip() or 0) or None
        elif sistema == "Windows":
            salida = _ejecutar(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                                "(Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfCores -Sum).Sum"], 12)
            n = int(salida.strip()) if salida.strip().isdigit() else None
    except (OSError, ValueError):
        n = None
    if not n:
        n = logicos // 2 if logicos >= 4 else logicos
    return max(1, min(n, logicos))


def resumen() -> dict:
    return {**memoria(), "nucleos_fisicos": nucleos_fisicos(), "nucleos_logicos": os.cpu_count()}


def advertencias(r: dict, usa_modelo_grande: bool) -> list[tuple[str, str, str]]:
    """(tema, detalle, arreglo) cuando la memoria hace probable un funcionamiento muy lento."""
    salida = []
    libre, swap, total = r.get("disponible_mb"), r.get("swap_usado_mb"), r.get("swap_total_mb")
    if usa_modelo_grande and libre is not None and libre < 2000:
        salida.append(("memoria", f"Solo hay {libre} MB de RAM disponible y el modelo de IA necesita cerca de 1500 MB: las respuestas pueden tardar muchísimo.",
                       "Cierra aplicaciones (navegador, editores), o usa un modelo más pequeño."))
    if swap is not None and total and swap > 0.5 * total and swap > 1000:
        salida.append(("memoria", f"El equipo está usando {swap} MB de swap (memoria en disco, mucho más lenta que la RAM).",
                       "Es la causa más probable de que todo vaya lento: cierra programas o añade RAM."))
    return salida
