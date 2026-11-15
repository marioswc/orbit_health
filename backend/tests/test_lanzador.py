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
