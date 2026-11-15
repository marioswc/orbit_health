import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_la_auditoria_de_seguridad_termina_sin_fallos():
    env = {**os.environ, "ORBIT_AUDITORIA_SIN_RED": "1"}
    p = subprocess.run([sys.executable, str(RAIZ / "scripts" / "auditoria_seguridad.py")], cwd=RAIZ, env=env,
                       capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stdout[-1500:]
    assert "0 fallo(s)" in p.stdout and "[FALLO]" not in p.stdout


def test_la_auditoria_no_imprime_nunca_el_valor_de_una_clave():
    env = {**os.environ, "ORBIT_AUDITORIA_SIN_RED": "1"}
    p = subprocess.run([sys.executable, str(RAIZ / "scripts" / "auditoria_seguridad.py")], cwd=RAIZ, env=env,
                       capture_output=True, text=True, timeout=120)
    assert "sk-" not in p.stdout
