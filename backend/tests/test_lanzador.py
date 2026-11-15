import socket
import sys
from pathlib import Path

import pytest

from app import config

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))
import lanzador  # noqa: E402


def test_en_el_ejecutable_nunca_se_busca_un_env_fuera_de_la_carpeta_indicada(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delenv("ORBIT_ENV_FILE", raising=False)
    assert config._ruta_dotenv() is None                                   # sin indicación: no lee nada
    monkeypatch.setenv("ORBIT_ENV_FILE", "/home/x/.local/share/orbit-health/.env")
    assert config._ruta_dotenv() == Path("/home/x/.local/share/orbit-health/.env")


def test_sin_empaquetar_se_usa_el_env_de_la_raiz(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert config._ruta_dotenv() == config.RAIZ / ".env"


@pytest.mark.parametrize("sistema,fragmento", [("Linux", "orbit-health"), ("Darwin", "Application Support"), ("Windows", "ORBIT Health")])
def test_la_carpeta_de_datos_es_la_del_usuario_en_cada_sistema(monkeypatch, tmp_path, sistema, fragmento):
    monkeypatch.setattr(lanzador.platform, "system", lambda: sistema)
    monkeypatch.setattr(lanzador.Path, "home", classmethod(lambda cls: tmp_path))
    for v in ("XDG_DATA_HOME", "LOCALAPPDATA"):
        monkeypatch.delenv(v, raising=False)
    carpeta = lanzador.carpeta_de_datos()
    assert carpeta.is_dir() and fragmento in str(carpeta) and str(carpeta).startswith(str(tmp_path))


def test_elige_el_siguiente_puerto_si_el_primero_esta_ocupado():
    with socket.socket() as ocupado:
        ocupado.bind(("127.0.0.1", 0))
        ocupado.listen()
        puerto = ocupado.getsockname()[1]
        assert lanzador.puerto_libre(puerto) != puerto


def test_hay_orbit_es_falso_si_nadie_responde():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    assert lanzador.hay_orbit(puerto) is False


def test_el_lanzador_solo_escucha_en_loopback():
    fuente = (RAIZ / "scripts" / "lanzador.py").read_text(encoding="utf-8")
    assert 'host="127.0.0.1"' in fuente and "0.0.0.0" not in fuente


# ---------- ventana de aplicación (como una app nativa) ----------
@pytest.mark.parametrize("sistema,esperado", [
    ("Linux", "/usr/bin/microsoft-edge"), ("Darwin", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
])
def test_elige_un_navegador_chromium_si_lo_hay(monkeypatch, sistema, esperado):
    monkeypatch.setattr(lanzador.platform, "system", lambda: sistema)
    monkeypatch.setattr(lanzador.shutil, "which", lambda n: "/usr/bin/microsoft-edge" if n == "microsoft-edge" else None)
    monkeypatch.setattr(lanzador.Path, "is_file", lambda self: str(self) == esperado)
    assert lanzador.navegador_de_ventana() == esperado


def test_sin_chromium_devuelve_none_y_se_abre_el_navegador_normal(monkeypatch):
    monkeypatch.setattr(lanzador.platform, "system", lambda: "Linux")
    monkeypatch.setattr(lanzador.shutil, "which", lambda n: None)                  # p. ej. solo Firefox, que no tiene modo aplicación
    assert lanzador.navegador_de_ventana() is None


def test_en_windows_busca_edge_antes_que_chrome_en_su_carpeta_de_programas(monkeypatch):
    monkeypatch.setattr(lanzador.platform, "system", lambda: "Windows")
    monkeypatch.setenv("ProgramFiles(x86)", "C:/Program Files (x86)")
    monkeypatch.delenv("ProgramFiles", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setattr(lanzador.Path, "is_file", lambda self: str(self).endswith(".exe"))      # todos "existen": gana el primero de la lista
    elegido = lanzador.navegador_de_ventana()
    assert elegido.endswith("msedge.exe") and "Edge" in elegido                                  # Edge viene con Windows 10 y 11


def test_la_ventana_usa_un_perfil_propio_y_no_toca_el_del_usuario(tmp_path):
    cmd = lanzador.comando_de_ventana("/usr/bin/chromium", "http://127.0.0.1:3000", tmp_path)
    assert cmd[0] == "/usr/bin/chromium" and "--app=http://127.0.0.1:3000" in cmd
    assert f"--user-data-dir={tmp_path / 'ventana'}" in cmd                        # perfil aparte: no mezcla pestañas ni sesiones
    assert "--no-first-run" in cmd


def test_sin_consola_la_salida_va_a_un_archivo_de_registro(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    lanzador._asegurar_salida(tmp_path)
    print("hola desde el ejecutable sin consola")
    sys.stdout.flush()
    assert "hola desde el ejecutable" in (tmp_path / "orbit-health.log").read_text(encoding="utf-8")


# ---------- modelo de IA incrustado: dónde se busca y cómo se baja ----------
def test_encuentra_el_modelo_en_la_carpeta_de_datos_o_junto_al_programa(tmp_path, monkeypatch):
    monkeypatch.setattr(lanzador, "BASE", tmp_path / "paquete")
    monkeypatch.setattr(lanzador, "CONGELADO", False)
    datos = tmp_path / "datos"
    assert lanzador.buscar_modelo(datos) is None
    (datos / "modelos").mkdir(parents=True)
    pequeno = datos / "modelos" / "roto.gguf"
    pequeno.write_bytes(b"x")                                                       # demasiado chico: un archivo a medias no cuenta
    assert lanzador.buscar_modelo(datos) is None
    monkeypatch.setattr(lanzador, "MODELO_MIN_BYTES", 10)
    pequeno.write_bytes(b"x" * 20)
    assert lanzador.buscar_modelo(datos) == pequeno
    (tmp_path / "paquete" / "modelos").mkdir(parents=True)
    junto = tmp_path / "paquete" / "modelos" / "completo.gguf"
    junto.write_bytes(b"x" * 20)
    assert lanzador.buscar_modelo(datos) == junto                                   # el del paquete completo gana


def test_la_descarga_escribe_un_parcial_y_solo_al_terminar_lo_deja_listo(tmp_path, monkeypatch):
    import http.server
    import threading
    cuerpo = b"G" * 4096

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.send_header("Content-Length", str(len(cuerpo))); self.end_headers(); self.wfile.write(cuerpo)
        def log_message(self, *a): pass
    s = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    try:
        monkeypatch.setattr(lanzador, "MODELO_MIN_BYTES", 1000)
        destino = lanzador.descargar_modelo(tmp_path, f"http://127.0.0.1:{s.server_port}/m.gguf")
        assert destino.read_bytes() == cuerpo and not destino.with_suffix(".part").exists()
        monkeypatch.setattr(lanzador, "MODELO_MIN_BYTES", 10_000)                  # ahora "queda incompleto": no se deja un archivo usable
        with pytest.raises(SystemExit):
            lanzador.descargar_modelo(tmp_path / "otro", f"http://127.0.0.1:{s.server_port}/m.gguf")
        assert not list((tmp_path / "otro").rglob("*.gguf"))
    finally:
        s.shutdown()


# ---------- icono en el menú de aplicaciones de Linux ----------
@pytest.fixture
def hogar_linux(tmp_path, monkeypatch):
    monkeypatch.setattr(lanzador.platform, "system", lambda: "Linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "datos"))
    escritorio = tmp_path / "Escritorio"
    escritorio.mkdir()
    monkeypatch.setattr(lanzador, "_carpeta_del_escritorio", lambda: escritorio)
    monkeypatch.setattr(lanzador.subprocess, "run", lambda *a, **k: None)           # sin tocar el sistema real
    return tmp_path


def test_el_acceso_directo_cumple_el_estandar_y_agrupa_la_ventana_con_su_icono():
    t = lanzador.contenido_del_acceso("/opt/orbit/orbit-health", "/home/x/.local/share/icons/orbit-health.png")
    assert t.startswith("[Desktop Entry]") and "Type=Application" in t and "Name=ORBIT Health" in t
    assert 'Exec="/opt/orbit/orbit-health"' in t and "Icon=/home/x/.local/share/icons/orbit-health.png" in t
    assert f"StartupWMClass={lanzador.CLASE_VENTANA}" in t and "Terminal=false" in t        # misma clase que la ventana
    assert f"--class={lanzador.CLASE_VENTANA}" in lanzador.comando_de_ventana("/x", "http://127.0.0.1:3000", Path("/tmp"))


def test_instalar_el_acceso_crea_menu_escritorio_e_icono_solo_en_la_carpeta_del_usuario(hogar_linux):
    exe = hogar_linux / "app" / "orbit-health"
    exe.parent.mkdir()
    exe.write_text("x")
    creados = lanzador.instalar_acceso(str(exe))
    menu = hogar_linux / "datos" / "applications" / "orbit-health.desktop"
    icono = hogar_linux / "datos" / "orbit-health" / "icono.png"
    assert menu.is_file() and (hogar_linux / "Escritorio" / "orbit-health.desktop").is_file() and icono.is_file()
    assert icono.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"                                  # el icono real, no un archivo vacío
    assert menu.stat().st_mode & 0o111                                                      # ejecutable: el escritorio lo acepta como lanzador
    assert str(exe) in menu.read_text() and all(str(c).startswith(str(hogar_linux)) for c in creados)
    lanzador.instalar_acceso(str(exe))                                                      # repetirlo no falla ni duplica
    assert len(list((hogar_linux / "datos" / "applications").glob("*.desktop"))) == 1


def test_quitar_el_acceso_borra_lo_que_se_creo(hogar_linux):
    exe = hogar_linux / "orbit-health"
    exe.write_text("x")
    lanzador.instalar_acceso(str(exe))
    quitados = lanzador.quitar_acceso()
    assert len(quitados) == 3 and not list(hogar_linux.rglob("orbit-health.desktop")) and not list(hogar_linux.rglob("icono.png"))
    assert lanzador.quitar_acceso() == []


def test_en_un_sistema_desconocido_explica_que_no_sabe(monkeypatch):
    monkeypatch.setattr(lanzador.platform, "system", lambda: "FreeBSD")
    with pytest.raises(SystemExit, match="FreeBSD"):
        lanzador.instalar_acceso()


# ---------- Windows: accesos .lnk con PowerShell ----------
def test_en_windows_crea_accesos_en_inicio_y_escritorio_con_el_icono_del_exe(tmp_path, monkeypatch):
    escritorio = tmp_path / "Desktop"
    escritorio.mkdir()
    monkeypatch.setattr(lanzador.platform, "system", lambda: "Windows")
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))
    ordenes = []

    def falso(cmd, **k):
        ordenes.append(cmd)
        class R: returncode = 0; stdout = str(escritorio) + "\n"
        return R()
    monkeypatch.setattr(lanzador.subprocess, "run", falso)
    exe = str(tmp_path / "Mi carpeta" / "O'Brien" / "orbit-health.exe")
    creados = lanzador.instalar_acceso(exe)
    assert [c.name for c in creados] == ["ORBIT Health.lnk", "ORBIT Health.lnk"]
    assert "Start Menu" in str(creados[0]) and creados[1].parent == escritorio
    lnk = [o for o in ordenes if o[0] == "powershell" and "CreateShortcut" in o[-1]]
    assert len(lnk) == 2
    for o in lnk:
        assert "-ExecutionPolicy" in o and "$s.IconLocation=" in o[-1] and "orbit-health.exe,0" in o[-1]
        assert "O''Brien" in o[-1] and "O'Brien" not in o[-1].replace("O''Brien", "")             # la comilla simple se escapa


def test_en_windows_quitar_borra_los_dos_accesos(tmp_path, monkeypatch):
    escritorio = tmp_path / "Desktop"
    escritorio.mkdir()
    monkeypatch.setattr(lanzador.platform, "system", lambda: "Windows")
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))
    class R: returncode = 0; stdout = str(escritorio) + "\n"
    monkeypatch.setattr(lanzador.subprocess, "run", lambda *a, **k: R())
    menu, esc = lanzador._rutas_windows()
    menu.parent.mkdir(parents=True)
    menu.write_text("x"); esc.write_text("x")
    assert len(lanzador.quitar_acceso()) == 2 and not menu.exists() and not esc.exists()


# ---------- macOS: ORBIT Health.app ----------
def test_en_mac_crea_una_app_valida_que_lanza_el_programa_sin_terminal(tmp_path, monkeypatch):
    import plistlib
    monkeypatch.setattr(lanzador.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(lanzador.Path, "home", classmethod(lambda cls: tmp_path))
    exe = tmp_path / "con espacios" / "orbit-health"
    exe.parent.mkdir()
    exe.write_text("x")
    (app,) = lanzador.instalar_acceso(str(exe))
    assert app == tmp_path / "Applications" / "ORBIT Health.app"
    plist = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
    assert plist["CFBundleExecutable"] == "orbit-health" and plist["CFBundlePackageType"] == "APPL" and plist["CFBundleIconFile"] == "orbit.icns"
    arranque = app / "Contents" / "MacOS" / "orbit-health"
    assert arranque.stat().st_mode & 0o111 and arranque.read_text().startswith("#!/bin/bash")
    assert "'" + str(exe) + "'" in arranque.read_text()                                         # la ruta con espacios va entre comillas
    assert (app / "Contents" / "Resources" / "orbit.icns").is_file()
    lanzador.instalar_acceso(str(exe))                                                          # repetirlo no falla
    assert [c.name for c in lanzador.quitar_acceso()] == ["ORBIT Health.app"] and not app.exists()


def test_funciona_aunque_la_carpeta_de_iconos_del_sistema_sea_de_root(hogar_linux):
    """Caso real: ~/.local/share/icons pertenece a root. El acceso no debe tocarla."""
    icons = hogar_linux / "datos" / "icons" / "hicolor"
    icons.mkdir(parents=True)
    icons.parent.chmod(0o555)
    icons.chmod(0o555)
    try:
        exe = hogar_linux / "orbit-health"
        exe.write_text("x")
        creados = lanzador.instalar_acceso(str(exe))
        assert any(c.name == "orbit-health.desktop" for c in creados) and all("icons" not in str(c) for c in creados)
    finally:
        icons.chmod(0o755)
        icons.parent.chmod(0o755)
