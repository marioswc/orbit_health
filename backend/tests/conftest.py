import pytest
from fastapi.testclient import TestClient

from app import config, main


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "api.db"))
    monkeypatch.setattr(config, "RESPALDO_CADA_MIN", 0)
    monkeypatch.setattr(config, "DIR_RESPALDOS", str(tmp_path / "resp"))
    with TestClient(main.app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture()
def cliente_auth(tmp_path, monkeypatch):
    """API con autenticación activa. T1 comandante; T2, T3 y T4 tripulantes (PIN = 111111, 222222, ...)."""
    from app.repositorios.conexion import get_conn
    from app.servicios import auth

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "auth.db"))
    monkeypatch.setattr(config, "RESPALDO_CADA_MIN", 0)
    monkeypatch.setattr(config, "DIR_RESPALDOS", str(tmp_path / "resp"))
    monkeypatch.setattr(config, "AUTH_ACTIVA", True)
    monkeypatch.setattr(config, "PBKDF2_ITER", 1000)
    with TestClient(main.app) as c:
        conn = get_conn()
        for tid, rol, pin in (("T1", "comandante", "111111"), ("T2", "tripulante", "222222"),
                              ("T3", "tripulante", "333333"), ("T4", "tripulante", "444444")):
            auth.inscribir(conn, tid, rol, pin=pin)
        conn.close()

        def entrar(tid):
            pin = {"T1": "111111", "T2": "222222", "T3": "333333", "T4": "444444"}[tid]
            r = c.post("/api/auth/login", json={"tripulante_id": tid, "pin": pin})
            assert r.status_code == 200, r.text
            return {"Authorization": f"Bearer {r.json()['token']}"}

        c.entrar = entrar
        yield c


@pytest.fixture(autouse=True)
def _flujo_limpio():
    """El estado de las ventanas de sensores vive en memoria: cada prueba empieza limpia."""
    from app.servicios import flujo
    flujo.reiniciar()
    yield
    flujo.reiniciar()
