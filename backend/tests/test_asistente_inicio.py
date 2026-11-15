import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))
import poner_env  # noqa: E402


# ---------- poner_env: cambia una variable sin tocar lo demás ----------
def test_cambia_una_variable_existente_y_conserva_el_resto(tmp_path):
    f = tmp_path / ".env"
    f.write_text("ORBIT_AUTH=0\n# comentario\nORBIT_HOST=127.0.0.1\n", encoding="utf-8")
    poner_env.poner(f, "ORBIT_AUTH", "1")
    assert f.read_text() == "ORBIT_AUTH=1\n# comentario\nORBIT_HOST=127.0.0.1\n"


def test_descomenta_una_variable_o_la_agrega_si_no_estaba(tmp_path):
    f = tmp_path / ".env"
    f.write_text("# ORBIT_PRECALENTAR=1\n", encoding="utf-8")
    poner_env.poner(f, "ORBIT_PRECALENTAR", "0")
    poner_env.poner(f, "ORBIT_VOZ_ACTIVA", "1")
    assert f.read_text() == "ORBIT_PRECALENTAR=0\nORBIT_VOZ_ACTIVA=1\n"


def test_el_archivo_queda_con_permisos_600(tmp_path):
    f = tmp_path / ".env"
    poner_env.poner(f, "ORBIT_AUTH", "1")
    assert stat.S_IMODE(f.stat().st_mode) == 0o600


@pytest.mark.parametrize("clave,valor", [("PATH", "x"), ("orbit_auth", "1"), ("ORBIT_X; rm -rf /", "1"), ("ORBIT_AUTH", "1\nPATH=/tmp")])
def test_rechaza_nombres_raros_y_valores_con_saltos_de_linea(tmp_path, clave, valor):
    f = tmp_path / ".env"
    with pytest.raises(ValueError):
        poner_env.poner(f, clave, valor)
    assert not f.exists()


def test_una_clave_leida_de_la_entrada_estandar_no_se_imprime(tmp_path):
    f = tmp_path / ".env"
    p = subprocess.run([sys.executable, str(RAIZ / "scripts" / "poner_env.py"), "ORBIT_DEEPSEEK_API_KEY", "-", str(f)],
                       input="sk-clave-secreta-de-prueba\n", capture_output=True, text=True)
    assert p.returncode == 0 and "sk-clave" not in p.stdout + p.stderr
    assert "ORBIT_DEEPSEEK_API_KEY=sk-clave-secreta-de-prueba" in f.read_text()


# ---------- el asistente de inicio ----------
def _correr(*args, entrada=""):
    return subprocess.run(["bash", str(RAIZ / "scripts" / "asistente_inicio.sh"), *args], cwd=RAIZ, input=entrada,
                          capture_output=True, text=True, timeout=60)


def test_la_simulacion_recorre_todos_los_pasos_sin_cambiar_nada():
    env = RAIZ / ".env"
    antes = env.read_text() if env.exists() else None
    p = _correr("--simular", "--sin-preguntas")
    assert p.returncode == 0, p.stdout + p.stderr
    for paso in ("1)", "2)", "3)", "4)", "5)", "6)"):
        assert paso in p.stdout
    assert "SIMULADO" in p.stdout and "no sustituye a un médico" in p.stdout
    assert (env.read_text() if env.exists() else None) == antes          # simular no escribe nada


def test_en_ingles_y_con_sin_preguntas_nunca_arranca_el_servidor():
    p = _correr("--simular", "--sin-preguntas", "--en")
    assert p.returncode == 0 and "setup assistant" in p.stdout and "Everything in this demo is SIMULATED" in p.stdout
    assert "(simulación) ./run.sh" not in p.stdout                       # con --sin-preguntas no se arranca


def test_responder_si_a_todo_en_simulacion_muestra_cada_instalacion():
    p = _correr("--simular", entrada="s\n1\ns\ns\n")                      # PIN sí, IA local, voz sí, arrancar sí
    assert p.returncode == 0, p.stdout
    for esperado in ("cuentas_demo.sh", "ORBIT_AUTH 1", "instalar_ia_local.sh", "ORBIT_IA_PROVEEDOR local",
                     "instalar_voz_local.sh", "ORBIT_VOZ_ACTIVA 1", "./run.sh"):
        assert esperado in p.stdout, esperado
