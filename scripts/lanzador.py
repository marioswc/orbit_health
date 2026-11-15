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


MODELO_URL = "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
MODELO_ARCHIVO = "qwen2.5-1.5b-instruct-q4_k_m.gguf"      # Qwen2.5 1.5B Instruct, licencia Apache-2.0, ~1.1 GB
MODELO_MIN_BYTES = 500_000_000


def buscar_modelo(datos: Path) -> Path | None:
    """Un modelo .gguf en `modelos/` junto al programa (paquete completo) o en la carpeta de datos del usuario."""
    junto = Path(sys.executable).resolve().parent if CONGELADO else BASE
    for carpeta in (junto / "modelos", datos / "modelos"):
        if carpeta.is_dir():
            encontrados = sorted(p for p in carpeta.glob("*.gguf") if p.is_file() and p.stat().st_size > MODELO_MIN_BYTES)
            if encontrados:
                return encontrados[0]
    return None


def descargar_modelo(datos: Path, url: str = MODELO_URL) -> Path:
    """Baja el modelo una vez (necesita internet) a la carpeta de datos. Escribe en un .part y lo renombra al terminar, para que
    nunca se use un archivo a medias."""
    destino = datos / "modelos" / MODELO_ARCHIVO
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(".part")
    print(f"Descargando el modelo de IA (~1.1 GB, una sola vez) a {destino} ...")
    with urllib.request.urlopen(url, timeout=60) as r, open(parcial, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        hecho, ultimo = 0, 0
        while bloque := r.read(1 << 20):
            f.write(bloque)
            hecho += len(bloque)
            if total and hecho - ultimo >= 50 << 20:
                ultimo = hecho
                print(f"  {hecho * 100 // total}%", flush=True)
    if parcial.stat().st_size < MODELO_MIN_BYTES:
        parcial.unlink(missing_ok=True)
        raise SystemExit("La descarga quedó incompleta; vuelve a intentarlo.")
    parcial.replace(destino)
    print("Listo: el modelo quedó instalado.")
    return destino


CLASE_VENTANA = "ORBITHealth"          # igual a StartupWMClass del acceso directo: así la barra de tareas agrupa la ventana con su icono


def _carpeta_del_escritorio() -> Path | None:
    try:
        r = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, timeout=3)
        c = Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else Path.home() / "Desktop"
    except (OSError, subprocess.SubprocessError):
        c = Path.home() / "Desktop"
    return c if c.is_dir() else None


def contenido_del_acceso(ejecutable: str, icono: str) -> str:
    """Archivo .desktop (estándar freedesktop): hace que ORBIT aparezca en el menú de aplicaciones con su icono."""
    return ("[Desktop Entry]\nType=Application\nVersion=1.0\nName=ORBIT Health\n"
            "GenericName=Apoyo a la salud de la tripulación\n"
            "Comment=Apoyo a la salud y el bienestar de una tripulación lejos de la Tierra (simulado, prototipo)\n"
            f'Exec="{ejecutable}"\nIcon={icono}\nTerminal=false\nCategories=Science;MedicalSoftware;\n'
            f"StartupWMClass={CLASE_VENTANA}\nStartupNotify=true\n")


def _ruta_ejecutable(ejecutable: str | None) -> str:
    return str(Path(ejecutable or (sys.executable if CONGELADO else Path(__file__).resolve())).resolve())


def _icono_png() -> Path | None:
    for c in (BASE / "frontend" / "dist" / "icono-512.png", BASE / "frontend" / "public" / "icono-512.png"):
        if c.is_file():
            return c
    return None


def _datos_usuario_linux() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def _acceso_linux(exe: str) -> list[Path]:
    origen = _icono_png()
    datos_usuario = _datos_usuario_linux()
    icono = datos_usuario / "orbit-health" / "icono.png"      # carpeta propia: ~/.local/share/icons suele ser de root y no se puede escribir
    icono.parent.mkdir(parents=True, exist_ok=True)
    if origen:
        shutil.copyfile(origen, icono)
    texto = contenido_del_acceso(exe, str(icono))
    creados = [icono]
    destinos = [datos_usuario / "applications" / "orbit-health.desktop"]
    escritorio = _carpeta_del_escritorio()
    if escritorio:
        destinos.append(escritorio / "orbit-health.desktop")
    for d in destinos:
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(texto, encoding="utf-8")
        d.chmod(0o755)                                   # el escritorio solo lo trata como lanzador si es ejecutable
        creados.append(d)
    if escritorio:                                       # GNOME pide marcar el lanzador del escritorio como "de confianza" para mostrar el icono
        try:
            subprocess.run(["gio", "set", str(destinos[-1]), "metadata::trusted", "true"], capture_output=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            pass
    for orden in (["update-desktop-database", str(destinos[0].parent)],):
        try:
            subprocess.run(orden, capture_output=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            pass
    return creados


def _ps(texto: str) -> str:
    return texto.replace("'", "''")                      # comilla simple dentro de una cadena de PowerShell


def _rutas_windows() -> tuple[Path, Path | None]:
    menu = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "ORBIT Health.lnk"
    escritorio = None
    try:                                                  # respeta un Escritorio redirigido (por ejemplo a OneDrive)
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", "[Environment]::GetFolderPath('Desktop')"],
                           capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and r.stdout.strip():
            escritorio = Path(r.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    escritorio = escritorio or Path.home() / "Desktop"
    return menu, (escritorio / "ORBIT Health.lnk" if escritorio.is_dir() else None)


def _acceso_windows(exe: str) -> list[Path]:
    """Accesos .lnk en el menú Inicio y el Escritorio, con el icono que ya va dentro del .exe (se crean con el propio PowerShell)."""
    menu, escritorio = _rutas_windows()
    creados = []
    for destino in [menu] + ([escritorio] if escritorio else []):
        destino.parent.mkdir(parents=True, exist_ok=True)
        orden = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{_ps(str(destino))}');"
                 f"$s.TargetPath='{_ps(exe)}';$s.WorkingDirectory='{_ps(str(Path(exe).parent))}';"
                 f"$s.IconLocation='{_ps(exe)},0';$s.Description='ORBIT Health';$s.Save()")
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", orden],
                       check=True, capture_output=True, timeout=30)
        creados.append(destino)
    return creados


def _app_mac() -> Path:
    return Path.home() / "Applications" / "ORBIT Health.app"


def _acceso_mac(exe: str) -> list[Path]:
    """Crea `ORBIT Health.app` en ~/Applications: un paquete mínimo cuyo ejecutable lanza el programa. Al abrirse como app no sale
    ninguna ventana de Terminal, y Launchpad y el Dock muestran su icono."""
    import plistlib
    import shlex
    app = _app_mac()
    macos, recursos = app / "Contents" / "MacOS", app / "Contents" / "Resources"
    macos.mkdir(parents=True, exist_ok=True)
    recursos.mkdir(parents=True, exist_ok=True)
    arranque = macos / "orbit-health"
    arranque.write_text(f'#!/bin/bash\nexec {shlex.quote(exe)} "$@"\n', encoding="utf-8")
    arranque.chmod(0o755)
    for c in (BASE / "empaquetado" / "orbit.icns", Path(__file__).resolve().parents[1] / "empaquetado" / "orbit.icns"):
        if c.is_file():
            shutil.copyfile(c, recursos / "orbit.icns")
            break
    with open(app / "Contents" / "Info.plist", "wb") as fh:
        plistlib.dump({"CFBundleName": "ORBIT Health", "CFBundleDisplayName": "ORBIT Health", "CFBundleIdentifier": "org.orbithealth.app",
                       "CFBundleVersion": "0.1.0", "CFBundleShortVersionString": "0.1.0", "CFBundleExecutable": "orbit-health",
                       "CFBundleIconFile": "orbit.icns", "CFBundlePackageType": "APPL", "LSMinimumSystemVersion": "11.0",
                       "NSHighResolutionCapable": True, "LSApplicationCategoryType": "public.app-category.healthcare-fitness"}, fh)
    return [app]


def instalar_acceso(ejecutable: str | None = None) -> list[Path]:
    """Crea el acceso con icono para ORBIT en el sistema de quien lo usa: menú de aplicaciones y escritorio en Linux, menú Inicio y
    Escritorio en Windows, y una app en ~/Applications en Mac. Solo escribe en la carpeta del propio usuario."""
    exe = _ruta_ejecutable(ejecutable)
    sistema = platform.system()
    if sistema == "Linux":
        return _acceso_linux(exe)
    if sistema == "Windows":
        return _acceso_windows(exe)
    if sistema == "Darwin":
        return _acceso_mac(exe)
    raise SystemExit(f"No sé crear un acceso directo en {sistema}.")


def quitar_acceso() -> list[Path]:
    sistema = platform.system()
    if sistema == "Windows":
        menu, escritorio = _rutas_windows()
        candidatos = [menu] + ([escritorio] if escritorio else [])
    elif sistema == "Darwin":
        candidatos = [_app_mac()]
    else:
        du = _datos_usuario_linux()
        candidatos = [du / "applications" / "orbit-health.desktop", du / "orbit-health" / "icono.png"]
        escritorio = _carpeta_del_escritorio()
        if escritorio:
            candidatos.append(escritorio / "orbit-health.desktop")
    quitados = [c for c in candidatos if c.exists()]
    for c in quitados:
        shutil.rmtree(c) if c.is_dir() else c.unlink()
    return quitados


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
            "--window-size=1280,820", "--disable-features=Translate", f"--class={CLASE_VENTANA}"]


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
    for flujo in (sys.stdout, sys.stderr):                   # línea por línea (si no, un archivo de registro se llena al salir) y consola de Windows (cp1252): que un carácter raro nunca tumbe el programa
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        except Exception:  # noqa: BLE001
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description="ORBIT Health: servidor local y ventana de aplicación")
    ap.add_argument("--puerto", type=int, default=3000)
    ap.add_argument("--sin-navegador", action="store_true", help="solo el servidor: no abrir ninguna ventana")
    ap.add_argument("--navegador", action="store_true", help="abrir el navegador normal en vez de la ventana de aplicación")
    ap.add_argument("--diagnostico", action="store_true", help="escribe un informe de la configuración y del sistema (archivo en la carpeta de datos) y termina")
    ap.add_argument("--instalar-acceso", action="store_true", help="crea el icono en el menú de aplicaciones y el escritorio (Linux), menú Inicio y Escritorio (Windows) o ~/Applications (Mac)")
    ap.add_argument("--quitar-acceso", action="store_true", help="borra ese acceso directo")
    ap.add_argument("--descargar-modelo", action="store_true", help="baja el modelo de IA una sola vez (necesita internet) y termina")
    args = ap.parse_args()

    datos = carpeta_de_datos()
    _asegurar_salida(datos)
    if args.instalar_acceso:
        for c in instalar_acceso():
            print("creado:", c)
        print("Listo: busca \"ORBIT Health\" en tu menú de aplicaciones. Si no aparece al instante, cierra y abre sesión.")
        return 0
    if args.quitar_acceso:
        for c in quitar_acceso():
            print("borrado:", c)
        return 0
    if args.descargar_modelo:
        descargar_modelo(datos)
        return 0
    os.environ.setdefault("ORBIT_DB_PATH", str(datos / "orbit_health.db"))
    os.environ.setdefault("ORBIT_DIR_RESPALDOS", str(datos / "respaldos"))
    os.environ.setdefault("ORBIT_ENV_FILE", str(datos / ".env"))
    dist = BASE / "frontend" / "dist"
    if dist.is_dir():
        os.environ.setdefault("ORBIT_FRONTEND_DIST", str(dist))
    if not CONGELADO:
        sys.path.insert(0, str(BASE / "backend"))
    modelo = buscar_modelo(datos)
    if modelo and "ORBIT_IA_MODELO_GGUF" not in os.environ:
        os.environ["ORBIT_IA_MODELO_GGUF"] = str(modelo)        # IA incrustada: el motor corre dentro del programa
        os.environ.setdefault("ORBIT_IA_PROVEEDOR", "local")    # y nada sale de la computadora aunque haya una clave de nube

    navegador = None if (args.sin_navegador or args.navegador) else navegador_de_ventana()

    if args.diagnostico:                                     # un informe que se puede enviar: sin secretos
        from app.servicios import diagnostico
        d = diagnostico.reunir()
        extra = [f"Ejecutable: {sys.executable}", f"Carpeta de datos: {datos}", f"Navegador para la ventana de aplicación: {navegador or 'ninguno (se usará el navegador normal)'}",
                 f"Modelo de IA encontrado: {modelo or 'no'}"]
        if platform.system() == "Darwin":
            extra.append(f"macOS {platform.mac_ver()[0]} en {platform.machine()} (este programa es solo arm64 y pide macOS 11 o posterior)")
            try:
                q = subprocess.run(["xattr", "-l", sys.executable], capture_output=True, text=True, timeout=5).stdout
                extra.append("Marca de cuarentena (bloqueo de Gatekeeper): " + ("SÍ, ver docs/EJECUTABLE.md" if "com.apple.quarantine" in q else "no"))
            except (OSError, subprocess.SubprocessError):
                pass
        texto = diagnostico.como_texto(d) + "\n\nDEL LANZADOR:\n  " + "\n  ".join(extra)
        informe = datos / "diagnostico.txt"
        informe.write_text(texto, encoding="utf-8")
        print(texto)
        print(f"\nInforme guardado en: {informe}")
        return 0

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
    print(f" IA incrustada: {modelo.name}" if modelo else " IA incrustada: no hay modelo (Nova usa textos escritos). Instálalo con --descargar-modelo")
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
