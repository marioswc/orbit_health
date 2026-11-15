"""La configuración nunca debe fallar en silencio: valores válidos se aceptan en cualquier forma razonable y los inválidos
detienen el arranque diciendo QUÉ variable está mal. Se prueba en un proceso aparte porque se lee al importar."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app import config

BACKEND = Path(__file__).resolve().parents[1]


def _importar(entorno: dict, dotenv: str | None = None, tmp: Path | None = None) -> subprocess.CompletedProcess:
    """Importa app.config en un proceso limpio con SOLO estas variables ORBIT_* y devuelve el resultado en JSON."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("ORBIT_")}
    env["ORBIT_ENV_FILE"] = str(tmp / ".env") if tmp else "/no/existe/.env"
    if dotenv is not None and tmp is not None:
        (tmp / ".env").write_text(dotenv, encoding="utf-8")
    env.update(entorno)
    codigo = ("import json; from app import config as c; print(json.dumps({'auth': c.AUTH_ACTIVA, 'voz': c.VOZ_ACTIVA, "
              "'seed': c.SEED_DEMO, 'iter': c.PBKDF2_ITER, 'leidas': c.variables_leidas()}))")
    return subprocess.run([sys.executable, "-c", codigo], cwd=BACKEND, env=env, capture_output=True, text=True, timeout=60)


def _auth(valor: str) -> bool:
    r = _importar({"ORBIT_AUTH": valor})
    assert r.returncode == 0, r.stderr[-400:]
    return json.loads(r.stdout)["auth"]


@pytest.mark.parametrize("valor", ["1", "true", "TRUE", "True", "yes", "on", "si", "sí", '"1"', "'true'", " 1 ", "1   # activar PIN"])
def test_cualquier_forma_razonable_de_decir_si_activa_la_autenticacion(valor):
    assert _auth(valor) is True


@pytest.mark.parametrize("valor", ["0", "false", "FALSE", "no", "off", '"0"', "", "0  # sin PIN"])
def test_cualquier_forma_razonable_de_decir_no_la_deja_apagada(valor):
    assert _auth(valor) is False


@pytest.mark.parametrize("valor", ["maybe", "2", "activo", "verdad"])
def test_un_valor_inventado_detiene_el_arranque_y_nombra_la_variable(valor):
    r = _importar({"ORBIT_AUTH": valor})
    assert r.returncode != 0
    assert "ORBIT_AUTH" in r.stderr and "no es un valor" in r.stderr and valor in r.stderr


def test_un_numero_invalido_dice_que_variable_es():
    r = _importar({"ORBIT_PBKDF2_ITER": "muchas"})
    assert r.returncode != 0 and "ORBIT_PBKDF2_ITER" in r.stderr and "entero" in r.stderr


def test_una_opcion_cerrada_invalida_lista_las_validas():
    r = _importar({"ORBIT_IA_PROVEEDOR": "ollama"})
    assert r.returncode != 0 and "ORBIT_IA_PROVEEDOR" in r.stderr and "deepseek" in r.stderr and "local" in r.stderr


def test_el_entorno_gana_al_dotenv_y_el_origen_queda_registrado(tmp_path):
    r = _importar({"ORBIT_PBKDF2_ITER": "1234"}, dotenv="ORBIT_PBKDF2_ITER=999\nORBIT_VOZ_ACTIVA=true\nORBIT_SEED_DEMO=0\n", tmp=tmp_path)
    assert r.returncode == 0, r.stderr[-300:]
    d = json.loads(r.stdout)
    assert d["iter"] == 1234                                           # lo definido en el entorno (Docker, systemd…) manda
    assert d["voz"] is True and d["seed"] is False                     # lo demás viene del .env
    assert d["leidas"]["ORBIT_PBKDF2_ITER"]["origen"] == "entorno"
    assert d["leidas"]["ORBIT_VOZ_ACTIVA"]["origen"] == ".env"
    assert d["leidas"]["ORBIT_AUTH"] == {"valor": None, "origen": "defecto"}


def test_la_clave_de_la_nube_nunca_aparece_en_el_resumen():
    r = _importar({"ORBIT_DEEPSEEK_API_KEY": "sk-secreta-123456"})
    assert "sk-secreta" not in r.stdout and json.loads(r.stdout)["leidas"]["ORBIT_DEEPSEEK_API_KEY"]["valor"] == "***"


def test_un_valor_vacio_cuenta_como_no_definido():
    r = _importar({"ORBIT_VOZ_ACTIVA": "", "ORBIT_PBKDF2_ITER": ""})
    assert r.returncode == 0 and json.loads(r.stdout)["iter"] == 200000


# ---------- el lector de .env ----------
def test_el_lector_de_dotenv_entiende_comillas_comentarios_export_y_bom(tmp_path):
    f = tmp_path / ".env"
    f.write_bytes("\ufeff# comentario\nORBIT_A=1\nORBIT_B=\"con espacios\"\nexport ORBIT_C='x'\nORBIT_D=valor   # nota\n\nsin_igual\n".encode("utf-8"))
    assert config.leer_dotenv(f) == {"ORBIT_A": "1", "ORBIT_B": "con espacios", "ORBIT_C": "x", "ORBIT_D": "valor"}


def test_una_almohadilla_sin_espacio_previo_forma_parte_del_valor(tmp_path):
    f = tmp_path / ".env"
    f.write_text("ORBIT_URL=http://x/#ancla\n", encoding="utf-8")
    assert config.leer_dotenv(f)["ORBIT_URL"] == "http://x/#ancla"      # como hace Docker Compose
