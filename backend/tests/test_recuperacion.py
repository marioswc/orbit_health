import sqlite3
import time

from app import config
from app.repositorios import conexion as db
from app.repositorios.respaldo import respaldar
from app.servicios import recuperacion as rec


def _base(ruta, filas=1):
    db.init_db(str(ruta))
    c = db.get_conn(str(ruta))
    for i in range(filas):
        c.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES (?,?,?,?)", (f"T{i}", "x", "y", "1990-01-01"))
    c.commit(); c.close()


def _corromper(ruta):
    with open(ruta, "r+b") as f:
        f.seek(0)
        f.write(b"ESTO NO ES SQLITE" * 40)


def test_base_sana_no_se_toca(tmp_path):
    _base(tmp_path / "o.db")
    assert rec.arranque_seguro(str(tmp_path / "o.db"), tmp_path / "r")["estado"] == "sana"


def test_sin_base_se_crea_nueva(tmp_path):
    assert rec.arranque_seguro(str(tmp_path / "no.db"), tmp_path / "r")["estado"] == "nueva"


def test_base_danada_se_restaura_desde_el_ultimo_respaldo_bueno_y_se_conserva_la_danada(tmp_path):
    ruta = tmp_path / "o.db"
    _base(ruta, filas=2)
    respaldar(tmp_path / "r", origen=str(ruta))
    _corromper(ruta)
    r = rec.arranque_seguro(str(ruta), tmp_path / "r")
    assert r["estado"] == "restaurada"
    c = sqlite3.connect(ruta)
    assert c.execute("SELECT COUNT(*) FROM tripulantes").fetchone()[0] == 2
    c.close()
    assert list(tmp_path.glob("o.db.danada-*"))                # la evidencia no se borra


def test_si_el_respaldo_mas_reciente_esta_danado_usa_el_anterior(tmp_path):
    ruta = tmp_path / "o.db"
    _base(ruta, filas=1)
    bueno = respaldar(tmp_path / "r", origen=str(ruta))
    time.sleep(0.01)
    malo = respaldar(tmp_path / "r", origen=str(ruta))
    _corromper(malo)
    _corromper(ruta)
    r = rec.arranque_seguro(str(ruta), tmp_path / "r")
    assert r["estado"] == "restaurada" and r["respaldo"] == bueno.name


def test_sin_respaldo_valido_el_sistema_igual_puede_iniciar(tmp_path):
    ruta = tmp_path / "o.db"
    _base(ruta)
    _corromper(ruta)
    r = rec.arranque_seguro(str(ruta), tmp_path / "r")
    assert r["estado"] == "reiniciada" and not ruta.exists()    # base nueva la crea init_db
    db.init_db(str(ruta))
    assert rec.verificar(ruta)[0] is True


def test_la_API_arranca_sola_con_una_base_danada_y_lo_informa(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main
    ruta = tmp_path / "api.db"
    _base(ruta, filas=1)
    respaldar(tmp_path / "resp", origen=str(ruta))
    _corromper(ruta)
    monkeypatch.setattr(config, "DB_PATH", str(ruta))
    monkeypatch.setattr(config, "DIR_RESPALDOS", str(tmp_path / "resp"))
    monkeypatch.setattr(config, "RESPALDO_CADA_MIN", 0)
    with TestClient(main.app) as c:
        s = c.get("/api/salud").json()
        assert s["base_ok"] is True and s["arranque"]["estado"] == "restaurada"
        assert c.get("/api/tripulantes").status_code == 200


def test_endpoint_salud_reporta_respaldos(cliente):
    s = cliente.get("/api/salud").json()
    assert s["base_ok"] is True and s["respaldos"] == 0
