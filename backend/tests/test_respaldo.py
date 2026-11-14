import sqlite3

from app.repositorios import conexion as db
from app.repositorios.respaldo import respaldar


def _base(tmp_path):
    ruta = str(tmp_path / "o.db")
    db.init_db(ruta)
    c = db.get_conn(ruta)
    c.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES ('T1','x','y','1990-01-01')")
    c.commit(); c.close()
    return ruta


def test_respaldo_es_una_copia_integra(tmp_path):
    ruta = _base(tmp_path)
    copia = respaldar(tmp_path / "r", origen=ruta)
    c = sqlite3.connect(copia)
    assert c.execute("SELECT COUNT(*) FROM tripulantes").fetchone()[0] == 1
    assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    c.close()


def test_respaldo_rota_copias_antiguas(tmp_path):
    ruta = _base(tmp_path)
    for _ in range(5):
        respaldar(tmp_path / "r", origen=ruta, conservar=3)
    assert len(list((tmp_path / "r").glob("orbit_health_*.db"))) == 3
