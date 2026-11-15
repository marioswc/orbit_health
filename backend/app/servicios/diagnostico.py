"""Diagnóstico del despliegue: qué configuración recibió DE VERDAD el programa, de dónde salió cada valor y qué está mal.

Pensado para tres casos reales: «las variables no llegan al contenedor», «la voz no funciona en el ejecutable» y «en Mac no
abre». Sirve igual desde la terminal (`python -m app.diagnostico`), desde el ejecutable (`orbit-health --diagnostico`, que además
lo guarda en un archivo para poder enviarlo) y desde la API (`GET /api/sistema/diagnostico`, solo el comandante con login activo).
Nunca imprime secretos: las claves salen como `***`.
"""
from __future__ import annotations

import difflib
import os
import platform
import shutil
import sys
from pathlib import Path

from .. import config
from . import ia_embebida, recursos, voz_local


def _escribible(carpeta: Path) -> bool:
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        prueba = carpeta / ".orbit-escritura"
        prueba.write_text("x")
        prueba.unlink()
        return True
    except OSError:
        return False


def _en_contenedor() -> bool:
    return Path("/.dockerenv").exists() or bool(os.environ.get("container"))


def _aviso(nivel: str, tema: str, detalle: str, arreglo: str = "") -> dict:
    return {"nivel": nivel, "tema": tema, "detalle": detalle, **({"arreglo": arreglo} if arreglo else {})}


def _variables_mal_escritas(advertencias: list[dict], dotenv: dict[str, str]) -> None:
    conocidas = set(config._LEIDAS) | set(config.VARIABLES_EXTERNAS)
    for nombre in sorted({k for k in os.environ if k.startswith("ORBIT_")} | set(dotenv)):
        if nombre in conocidas:
            continue
        cerca = difflib.get_close_matches(nombre.upper(), conocidas, n=1, cutoff=0.8 if not nombre.startswith("ORBIT_") else 0.75)
        if nombre.startswith("ORBIT_") or cerca:        # una clave ajena (PATH, HOME…) en el .env no es asunto nuestro
            advertencias.append(_aviso("aviso", "variable desconocida",
                                       f"{nombre} no la lee el programa: se ignora en silencio." + (f" ¿Quisiste decir {cerca[0]}?" if cerca else ""),
                                       f"Corrige el nombre a {cerca[0]}." if cerca else "Bórrala o revisa .env.example."))


def reunir() -> dict:
    ruta_env = config._ruta_dotenv()
    dotenv: dict[str, str] = {}
    if ruta_env and ruta_env.is_file():
        try:
            dotenv = config.leer_dotenv(ruta_env)
        except (OSError, UnicodeDecodeError):
            pass
    db = Path(config.DB_PATH)
    dist = Path(config.FRONTEND_DIST) if config.FRONTEND_DIST else config.RAIZ / "frontend" / "dist"
    voz = voz_local.estado_voz()
    ia = {"embebida": {"modelo": config.IA_MODELO_GGUF or None, "disponible": ia_embebida.disponible()},
          "ollama": {"url": config.IA_LOCAL_URL or None, "modelo": config.IA_LOCAL_MODELO or None},
          "nube": {"clave_definida": bool(config.DEEPSEEK_API_KEY), "proveedor": config.IA_PROVEEDOR or "(vacío)"},
          "cpus": os.cpu_count(), "hilos_embebida": config.IA_HILOS or "automático"}
    adv: list[dict] = []
    _variables_mal_escritas(adv, dotenv)
    if config.VOZ_ACTIVA and not voz["lista"]:
        adv.append(_aviso("aviso", "voz", voz["detalle"], "scripts/instalar_voz_local.sh (necesita internet una vez)"))
    if config.IA_MODELO_GGUF and not Path(config.IA_MODELO_GGUF).is_file():
        adv.append(_aviso("aviso", "IA incrustada", f"ORBIT_IA_MODELO_GGUF apunta a un archivo que no existe: {config.IA_MODELO_GGUF}"))
    if config.IA_PROVEEDOR == "local" and not (ia["embebida"]["disponible"] or config.IA_LOCAL_URL):
        adv.append(_aviso("aviso", "IA", "ORBIT_IA_PROVEEDOR=local pero no hay modelo incrustado ni ORBIT_IA_LOCAL_URL: Nova usará textos escritos."))
    if config.DEEPSEEK_API_KEY and config.IA_PROVEEDOR != "local":
        adv.append(_aviso("aviso", "privacidad", "Hay una clave de DeepSeek y el proveedor no es 'local': las preguntas SALEN de la estación.",
                          "Pon ORBIT_IA_PROVEEDOR=local para que nada salga."))
    if config.AUTH_ACTIVA and config.SEED_DEMO:
        adv.append(_aviso("aviso", "seguridad", "Autenticación activa con la siembra de demostración encendida: existen cuentas con PIN público (111111…).",
                          "En una instalación real pon ORBIT_SEED_DEMO=0."))
    if not _escribible(db.parent):
        adv.append(_aviso("error", "datos", f"No se puede escribir en la carpeta de la base de datos: {db.parent}", "Revisa permisos o define ORBIT_DB_PATH."))
    if not (dist / "index.html").is_file():
        adv.append(_aviso("aviso", "interfaz", f"No hay interfaz compilada en {dist}: solo funcionará la API.", "cd frontend && npm run build"))
    if _en_contenedor() and os.environ.get("ORBIT_HOST", "").strip() in ("127.0.0.1", "localhost", "::1"):
        adv.append(_aviso("info", "contenedor", "ORBIT_HOST=127.0.0.1 no afecta a un contenedor: ahí se escucha en ORBIT_CONTENEDOR_HOST (0.0.0.0) y el acceso externo lo limita docker-compose.yml."))
    if _en_contenedor() and config.IA_LOCAL_URL and any(h in config.IA_LOCAL_URL for h in ("127.0.0.1", "localhost")):
        adv.append(_aviso("info", "contenedor", "ORBIT_IA_LOCAL_URL apunta a 127.0.0.1: dentro del contenedor se traduce a host.docker.internal (tu computadora).",
                          "En Linux, Ollama debe escuchar fuera de localhost (OLLAMA_HOST=0.0.0.0) o usa el modelo incrustado (ORBIT_IA_MODELO_GGUF)."))
    rec = recursos.resumen()
    for tema, detalle, arreglo in recursos.advertencias(rec, usa_modelo_grande=ia["embebida"]["disponible"] or bool(config.IA_LOCAL_URL)):
        adv.append(_aviso("aviso", tema, detalle, arreglo))
    return {
        "recursos": rec,
        "sistema": {"os": platform.system(), "version": platform.version()[:80], "arquitectura": platform.machine(), "python": sys.version.split()[0],
                    "ejecutable_empaquetado": bool(getattr(sys, "frozen", False)), "contenedor": _en_contenedor(), "cpus": os.cpu_count(),
                    "directorio_de_trabajo": str(Path.cwd())},
        "rutas": {"base_de_datos": {"ruta": str(db), "existe": db.is_file(), "carpeta_escribible": _escribible(db.parent)},
                  "respaldos": {"ruta": config.DIR_RESPALDOS}, "interfaz": {"ruta": str(dist), "existe": (dist / "index.html").is_file()},
                  "dotenv": {"ruta": str(ruta_env) if ruta_env else None, "existe": bool(ruta_env and ruta_env.is_file()), "variables": len(dotenv)}},
        "variables": config.variables_leidas(),
        "voz": voz, "ia": ia,
        "navegador_de_ventana": shutil.which("microsoft-edge") or shutil.which("google-chrome") or shutil.which("chromium"),
        "advertencias": adv,
    }


def como_texto(d: dict) -> str:
    s, r = d["sistema"], d["rutas"]
    l = ["DIAGNÓSTICO DE ORBIT HEALTH", "=" * 60,
         f"Sistema: {s['os']} {s['arquitectura']} | Python {s['python']} | CPUs {s['cpus']} | " +
         ("ejecutable empaquetado" if s["ejecutable_empaquetado"] else "código fuente") + (" | DENTRO DE UN CONTENEDOR" if s["contenedor"] else ""),
         f"Base de datos: {r['base_de_datos']['ruta']} (existe: {r['base_de_datos']['existe']}, escribible: {r['base_de_datos']['carpeta_escribible']})",
         f"Interfaz: {r['interfaz']['ruta']} (existe: {r['interfaz']['existe']})",
         f".env: {r['dotenv']['ruta']} (existe: {r['dotenv']['existe']}, {r['dotenv']['variables']} variables)",
         f"Memoria: total {d['recursos']['total_mb']} MB, disponible {d['recursos']['disponible_mb']} MB, swap usado {d['recursos']['swap_usado_mb']} de {d['recursos']['swap_total_mb']} MB | núcleos: {d['recursos']['nucleos_fisicos']} físicos, {d['recursos']['nucleos_logicos']} lógicos",
         f"Voz: {d['voz']['motivo']}: {d['voz']['detalle']}",
         f"IA: incrustada={d['ia']['embebida']['disponible']} ollama={d['ia']['ollama']['url'] or '-'} nube_clave={d['ia']['nube']['clave_definida']} proveedor={d['ia']['nube']['proveedor']}",
         "", "VARIABLES (valor | origen). 'defecto' = nadie la definió:"]
    for n, v in d["variables"].items():
        l.append(f"  {n:<34} {str(v['valor']) if v['valor'] is not None else '-':<28} {v['origen']}")
    l += ["", "ADVERTENCIAS:"] + ([f"  [{a['nivel'].upper()}] {a['tema']}: {a['detalle']}" + (f"  -> {a['arreglo']}" if a.get('arreglo') else "") for a in d["advertencias"]]
                                  or ["  Ninguna."])
    return "\n".join(l)
