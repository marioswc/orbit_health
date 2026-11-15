import json
import os
from pathlib import Path

import pytest

from app import config
from app.servicios import diagnostico, voz_local


@pytest.fixture(autouse=True)
def _sin_dotenv_ajeno(monkeypatch, tmp_path):
    """Las pruebas no deben depender del .env de quien las corre (que puede traer, por ejemplo, un nombre mal escrito)."""
    monkeypatch.setenv("ORBIT_ENV_FILE", str(tmp_path / "no-hay.env"))


def _temas(d: dict) -> list[str]:
    return [a["tema"] for a in d["advertencias"]]


# ---------- variables mal escritas: el caso real RBIT_HOST ----------
def test_detecta_una_variable_mal_escrita_en_el_entorno_y_sugiere_la_correcta(monkeypatch):
    monkeypatch.setenv("ORBIT_AUHT", "1")
    adv = [a for a in diagnostico.reunir()["advertencias"] if a["tema"] == "variable desconocida" and "ORBIT_AUHT" in a["detalle"]]
    assert len(adv) == 1 and "ORBIT_AUTH" in adv[0]["detalle"] and "ORBIT_AUTH" in adv[0]["arreglo"]


def test_detecta_en_el_dotenv_un_nombre_sin_la_O_inicial(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("RBIT_HOST=127.0.0.1\nPATH_EXTRA=/x\nORBIT_AUTH=1\n", encoding="utf-8")
    monkeypatch.setenv("ORBIT_ENV_FILE", str(f))
    d = diagnostico.reunir()
    detalles = " ".join(a["detalle"] for a in d["advertencias"])
    assert "RBIT_HOST" in detalles and "ORBIT_HOST" in detalles
    assert "PATH_EXTRA" not in detalles                                     # una clave ajena que no se parece a ninguna nuestra no es un error


def test_las_variables_externas_validas_no_se_marcan_como_desconocidas(monkeypatch):
    for n in ("ORBIT_HOST", "ORBIT_PUERTO", "ORBIT_CONTENEDOR_HOST"):
        monkeypatch.setenv(n, "x")
    assert "variable desconocida" not in _temas(diagnostico.reunir())


# ---------- advertencias de despliegue ----------
def test_avisa_de_la_clave_de_nube_sin_proveedor_local(monkeypatch):
    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "sk-x")
    monkeypatch.setattr(config, "IA_PROVEEDOR", "")
    assert "privacidad" in _temas(diagnostico.reunir())
    monkeypatch.setattr(config, "IA_PROVEEDOR", "local")
    assert "privacidad" not in _temas(diagnostico.reunir())


def test_avisa_de_pin_publico_con_autenticacion_y_siembra_de_demo(monkeypatch):
    monkeypatch.setattr(config, "AUTH_ACTIVA", True)
    monkeypatch.setattr(config, "SEED_DEMO", True)
    assert "seguridad" in _temas(diagnostico.reunir())
    monkeypatch.setattr(config, "SEED_DEMO", False)
    assert "seguridad" not in _temas(diagnostico.reunir())


def test_dentro_de_un_contenedor_avisa_de_que_ollama_en_127_0_0_1_no_es_el_del_anfitrion(monkeypatch):
    monkeypatch.setattr(diagnostico, "_en_contenedor", lambda: True)
    monkeypatch.setattr(config, "IA_LOCAL_URL", "http://127.0.0.1:11434/api/generate")
    assert "contenedor" in _temas(diagnostico.reunir())


def test_un_error_de_escritura_en_la_carpeta_de_datos_es_un_error_no_un_aviso(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "no" / "escribible" / "x.db"))
    monkeypatch.setattr(diagnostico, "_escribible", lambda c: False)
    assert any(a["nivel"] == "error" and a["tema"] == "datos" for a in diagnostico.reunir()["advertencias"])


def test_el_diagnostico_nunca_contiene_secretos(monkeypatch):
    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "sk-ultra-secreta-999")
    config._LEIDAS["ORBIT_DEEPSEEK_API_KEY"] = {"valor": "sk-ultra-secreta-999", "origen": "entorno"}
    assert "sk-ultra" not in json.dumps(diagnostico.reunir()) and "sk-ultra" not in diagnostico.como_texto(diagnostico.reunir())


# ---------- endpoint ----------
def test_el_endpoint_de_diagnostico_solo_lo_ve_el_comandante(cliente_auth):
    c = cliente_auth
    assert c.get("/api/sistema/diagnostico").status_code == 401
    assert c.get("/api/sistema/diagnostico", headers=c.entrar("T3")).status_code == 403
    r = c.get("/api/sistema/diagnostico", headers=c.entrar("T1"))
    assert r.status_code == 200 and {"sistema", "rutas", "variables", "voz", "ia", "advertencias"} <= set(r.json())


# ---------- estado de la voz: dice QUÉ falta, no un error genérico ----------
def test_voz_desactivada_se_explica_sin_alarma(monkeypatch):
    monkeypatch.setattr(config, "VOZ_ACTIVA", False)
    e = voz_local.estado_voz()
    assert e["motivo"] == "desactivada" and e["lista"] is False and "texto" in e["detalle"]


@pytest.mark.parametrize("modelo,motivo", [("", "sin_modelo"), ("/no/existe/whisper", "modelo_no_existe")])
def test_voz_activa_sin_modelo_dice_que_falta(monkeypatch, modelo, motivo):
    monkeypatch.setattr(config, "VOZ_ACTIVA", True)
    monkeypatch.setattr(config, "VOZ_STT_MODELO", modelo)
    monkeypatch.setattr("importlib.util.find_spec", lambda n: object())               # como si las librerías estuvieran instaladas
    assert voz_local.estado_voz()["motivo"] == motivo


def test_voz_sin_librerias_pide_instalar_el_paquete_de_voz(monkeypatch):
    monkeypatch.setattr(config, "VOZ_ACTIVA", True)
    monkeypatch.setattr("importlib.util.find_spec", lambda n: None)
    e = voz_local.estado_voz()
    assert e["motivo"] == "faltan_librerias" and "requirements-voice.txt" in e["detalle"]


def test_voz_lista_con_modelo_en_disco_pero_sin_piper_responde_con_texto(monkeypatch, tmp_path):
    (tmp_path / "whisper").mkdir()
    monkeypatch.setattr(config, "VOZ_ACTIVA", True)
    monkeypatch.setattr(config, "VOZ_STT_MODELO", str(tmp_path / "whisper"))
    monkeypatch.setattr(config, "VOZ_PIPER_BIN", "piper-que-no-existe")
    monkeypatch.setattr(config, "VOZ_PIPER_MODELO", "")
    monkeypatch.setattr(config, "VOZ_PIPER_MODELO_EN", "")
    monkeypatch.setattr("importlib.util.find_spec", lambda n: object())
    e = voz_local.estado_voz()
    assert e["lista"] is True and e["habla"] is False and "sin voz hablada" in e["detalle"]


def test_el_endpoint_de_estado_de_voz_existe_y_exige_sesion(cliente_auth):
    c = cliente_auth
    assert c.get("/api/voz/estado").status_code == 401
    r = c.get("/api/voz/estado", headers=c.entrar("T3"))
    assert r.status_code == 200 and "motivo" in r.json() and "detalle" in r.json()


# ---------- resolver rutas relativas: el motivo de que la voz fallara en el ejecutable y en Docker ----------
def test_una_ruta_relativa_se_busca_junto_a_la_base_de_datos(monkeypatch, tmp_path):
    datos = tmp_path / "datos"
    (datos / "models" / "whisper").mkdir(parents=True)
    monkeypatch.setenv("ORBIT_DB_PATH", str(datos / "orbit.db"))
    monkeypatch.chdir(tmp_path)                                                     # un directorio de trabajo cualquiera, como al hacer doble clic
    assert config.resolver_ruta("./models/whisper") == datos / "models" / "whisper"


def test_una_ruta_relativa_tambien_se_encuentra_en_el_directorio_de_trabajo(monkeypatch, tmp_path):
    (tmp_path / "modelos").mkdir()
    monkeypatch.setenv("ORBIT_DB_PATH", str(tmp_path / "otra" / "orbit.db"))
    monkeypatch.chdir(tmp_path)
    assert config.resolver_ruta("modelos") == tmp_path / "modelos"


def test_una_ruta_absoluta_se_respeta_y_una_inexistente_devuelve_la_primera_candidata(tmp_path):
    assert config.resolver_ruta(str(tmp_path / "x")) == tmp_path / "x"
    assert config.resolver_ruta("no-existe-en-ningun-lado").name == "no-existe-en-ningun-lado"
