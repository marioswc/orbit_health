#!/usr/bin/env python3
"""Lanzador de ORBIT Health: arranca el servidor en esta computadora y abre SU PROPIA VENTANA (modo aplicación, sin pestañas
ni barra de direcciones). Es el punto de entrada del ejecutable (doble clic) y también sirve sin empaquetar:
  python scripts/lanzador.py
La ventana usa el navegador basado en Chromium que ya traiga el sistema (Edge en Windows; Chrome, Edge, Chromium o Brave donde
estén). Al cerrar la ventana se apaga el servidor, como una app nativa. Si no hay ninguno, se abre el navegador normal.

Los datos de la persona (base, respaldos y .env) viven en SU carpeta de usuario, no dentro del programa:
  Linux  ~/.local/share/orbit-health     Mac  ~/Library/Application Support/ORBIT Health     Windows  %LOCALAPPDATA%\\ORBIT Health
Solo escucha en 127.0.0.1 (nadie más en la red ve los datos de salud).
"""
import argparse
import os
import platform
import shutil
import socket
import subprocess
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


def navegador_de_ventana() -> str | None:
    """Ruta de un navegador basado en Chromium (el único con modo aplicación fiable), o None."""
    sistema = platform.system()
    candidatos: list[str] = []
    if sistema == "Windows":
        bases = [os.environ.get(v) for v in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")]
        for b in filter(None, bases):
            candidatos += [str(Path(b) / r) for r in (r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe",
                                                       r"BraveSoftware\Brave-Browser\Application\brave.exe")]
    elif sistema == "Darwin":
        for app in ("Google Chrome", "Microsoft Edge", "Chromium", "Brave Browser"):
            candidatos.append(f"/Applications/{app}.app/Contents/MacOS/{app}")
    else:
        candidatos = [p for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge",
                                  "microsoft-edge-stable", "brave-browser") if (p := shutil.which(n))]
    return next((c for c in candidatos if Path(c).is_file()), None)


def comando_de_ventana(navegador: str, url: str, datos: Path) -> list[str]:
    """Comando para abrir la ventana de aplicación con un perfil propio (así es un proceso aparte que dura mientras la ventana
    esté abierta, y no toca el perfil ni las pestañas del navegador de la persona)."""
    return [navegador, f"--app={url}", f"--user-data-dir={datos / 'ventana'}", "--no-first-run", "--no-default-browser-check",
            "--window-size=1280,820", "--disable-features=Translate"]


def abrir_cuando_responda(url: str, puerto: int) -> None:
    for _ in range(80):
        if hay_orbit(puerto):
            webbrowser.open(url)
            return
        time.sleep(0.25)


def _asegurar_salida(datos: Path) -> None:
    """En el ejecutable sin consola (Windows y Mac) no hay stdout: se manda todo a un archivo de registro en la carpeta de datos."""
    if sys.stdout is None or sys.stderr is None:
        registro = open(datos / "orbit-health.log", "a", encoding="utf-8", buffering=1)  # noqa: SIM115
        sys.stdout = sys.stdout or registro
        sys.stderr = sys.stderr or registro
    for flujo in (sys.stdout, sys.stderr):                   # consola de Windows (cp1252): que un carácter raro nunca tumbe el programa
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description="ORBIT Health: servidor local y ventana de aplicación")
    ap.add_argument("--puerto", type=int, default=3000)
    ap.add_argument("--sin-navegador", action="store_true", help="solo el servidor: no abrir ninguna ventana")
    ap.add_argument("--navegador", action="store_true", help="abrir el navegador normal en vez de la ventana de aplicación")
    args = ap.parse_args()

    datos = carpeta_de_datos()
    _asegurar_salida(datos)
    os.environ.setdefault("ORBIT_DB_PATH", str(datos / "orbit_health.db"))
    os.environ.setdefault("ORBIT_DIR_RESPALDOS", str(datos / "respaldos"))
    os.environ.setdefault("ORBIT_ENV_FILE", str(datos / ".env"))
    dist = BASE / "frontend" / "dist"
    if dist.is_dir():
        os.environ.setdefault("ORBIT_FRONTEND_DIST", str(dist))
    if not CONGELADO:
        sys.path.insert(0, str(BASE / "backend"))

    navegador = None if (args.sin_navegador or args.navegador) else navegador_de_ventana()

    if hay_orbit(args.puerto):                               # ya está corriendo: solo abrir otra ventana, sin duplicar el servidor
        url = f"http://127.0.0.1:{args.puerto}"
        print(f"ORBIT Health ya estaba abierto en {url}")
        if navegador:
            subprocess.Popen(comando_de_ventana(navegador, url, datos))
        elif not args.sin_navegador:
            webbrowser.open(url)
        return 0
    puerto = puerto_libre(args.puerto)
    url = f"http://127.0.0.1:{puerto}"

    import uvicorn
    from app.main import app

    print("=" * 60)
    print(" ORBIT Health está arrancando")
    print(f" Se abrirá {'su ventana de aplicación' if navegador else 'el navegador'} en {url}")
    print(f" Tus datos se guardan en: {datos}")
    print(" Para detenerlo, cierra la ventana de ORBIT (o pulsa Ctrl+C aquí).")
    print(" Todo en esta demostración es SIMULADO; no sustituye a un médico.")
    print("=" * 60)
    servidor = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=puerto, log_level="warning"))

    if not navegador:
        if not (args.sin_navegador):
            threading.Thread(target=abrir_cuando_responda, args=(url, puerto), daemon=True).start()
        servidor.run()
        return 0

    hilo = threading.Thread(target=servidor.run, daemon=True)
    hilo.start()
    for _ in range(120):                                     # espera a que el servidor responda antes de abrir la ventana
        if hay_orbit(puerto):
            break
        time.sleep(0.25)
    inicio = time.monotonic()
    ventana = subprocess.Popen(comando_de_ventana(navegador, url, datos))
    try:
        ventana.wait()
        if time.monotonic() - inicio < 3:                    # el navegador delegó en otro proceso y salió: no se puede saber cuándo se cierra
            print("La ventana se abrió en otro proceso; el servidor sigue activo (Ctrl+C para detenerlo).")
            while hilo.is_alive():
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    servidor.should_exit = True                              # cerrar la ventana apaga el servidor, como una app nativa
    hilo.join(timeout=10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
