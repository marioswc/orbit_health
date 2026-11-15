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
