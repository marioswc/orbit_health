#!/usr/bin/env python3
"""Lanzador de ORBIT Health: arranca el servidor en esta computadora y abre el navegador. Es el punto de entrada del
ejecutable (doble clic) y también sirve sin empaquetar:  python scripts/lanzador.py

Los datos de la persona (base, respaldos y .env) viven en SU carpeta de usuario, no dentro del programa:
  Linux  ~/.local/share/orbit-health     Mac  ~/Library/Application Support/ORBIT Health     Windows  %LOCALAPPDATA%\\ORBIT Health
Solo escucha en 127.0.0.1 (nadie más en la red ve los datos de salud).
"""
import argparse
import os
import platform
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

CONGELADO = getattr(sys, "frozen", False)
BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def carpeta_de_datos() -> Path:
    sistema = platform.system()
    if sistema == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "ORBIT Health"
    elif sistema == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "ORBIT Health"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "orbit-health"
    base.mkdir(parents=True, exist_ok=True)
    return base


def hay_orbit(puerto: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/api/salud", timeout=1.5) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def puerto_libre(inicio: int) -> int:
    for p in range(inicio, inicio + 30):
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    raise SystemExit("No encontré un puerto libre entre %d y %d." % (inicio, inicio + 29))


def abrir_cuando_responda(url: str, puerto: int) -> None:
    for _ in range(80):
        if hay_orbit(puerto):
            webbrowser.open(url)
            return
        time.sleep(0.25)


def main() -> int:
    ap = argparse.ArgumentParser(description="ORBIT Health: servidor local y navegador")
    ap.add_argument("--puerto", type=int, default=3000)
    ap.add_argument("--sin-navegador", action="store_true", help="no abrir el navegador")
    args = ap.parse_args()

    datos = carpeta_de_datos()
    os.environ.setdefault("ORBIT_DB_PATH", str(datos / "orbit_health.db"))
    os.environ.setdefault("ORBIT_DIR_RESPALDOS", str(datos / "respaldos"))
    os.environ.setdefault("ORBIT_ENV_FILE", str(datos / ".env"))
    dist = BASE / "frontend" / "dist"
    if dist.is_dir():
        os.environ.setdefault("ORBIT_FRONTEND_DIST", str(dist))
    if not CONGELADO:
        sys.path.insert(0, str(BASE / "backend"))

    if hay_orbit(args.puerto):                               # ya está corriendo: solo abrirlo, sin duplicar
        print(f"ORBIT Health ya estaba abierto en http://127.0.0.1:{args.puerto}")
        if not args.sin_navegador:
            webbrowser.open(f"http://127.0.0.1:{args.puerto}")
        return 0
    puerto = puerto_libre(args.puerto)
    url = f"http://127.0.0.1:{puerto}"

    import uvicorn
    from app.main import app

    print("=" * 60)
    print(" ORBIT Health está arrancando")
    print(f" Se abrirá el navegador en {url}")
    print(f" Tus datos se guardan en: {datos}")
    print(" Para detenerlo, cierra esta ventana o pulsa Ctrl+C.")
    print(" Todo en esta demostración es SIMULADO; no sustituye a un médico.")
    print("=" * 60)
    if not args.sin_navegador:
        threading.Thread(target=abrir_cuando_responda, args=(url, puerto), daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=puerto, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
