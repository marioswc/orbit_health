from fastapi.testclient import TestClient

from app import db
from app.main import app


def test_health():
    assert TestClient(app).get("/api/health").json() == {"status": "ok"}


def test_schema_se_crea(tmp_path):
    ruta = str(tmp_path / "t.db")
    db.init_db(ruta)
    conn = db.get_conn(ruta)
    tablas = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"tripulantes", "lecturas", "cola_salida", "diario_privado", "tamizajes", "capsulas"} <= tablas
