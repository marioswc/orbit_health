from datetime import datetime, timezone

from app.fuentes import calibracion
from app.repositorios import conexion as db
from app.dominio import reglas as engine


def _csv(tmp_path, filas):
    p = tmp_path / "bidmc_99_Numerics.csv"
    p.write_text("Time [s], HR, PULSE, RESP, SpO2\n" + "\n".join(filas) + "\n", encoding="utf-8")
    return p


def test_mediana_por_ventana_y_descarta_invalidos(tmp_path):
    filas = [f"{i},70,70,16,98" for i in range(40)] + ["40,70,70,16,"]  # último SpO2 vacío
    s = calibracion.leer_numerics(_csv(tmp_path, filas))
    assert s["frecuencia_cardiaca"] == [70, 70, 70]       # 40 s en 2 ventanas + 1 fila suelta
    assert s["spo2"] == [98, 98]


def test_cargar_es_idempotente_y_no_toca_cola(tmp_path):
    ruta = _csv(tmp_path, [f"{i},{60 + i % 5},0,{14 + i % 3},{96 + i % 3}" for i in range(120)])
    dbp = str(tmp_path / "c.db")
    db.init_db(dbp)
    c = db.get_conn(dbp)
    c.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES ('T1','x','y','1990-01-01')")
    c.commit(); c.close()
    ahora = datetime(2026, 1, 15, tzinfo=timezone.utc)
    n1 = calibracion.cargar("T1", ruta, dbp, ahora)
    n2 = calibracion.cargar("T1", ruta, dbp, ahora)
    c = db.get_conn(dbp)
    total = c.execute("SELECT COUNT(*) FROM lecturas WHERE origen='calibracion'").fetchone()[0]
    cola = c.execute("SELECT COUNT(*) FROM cola_salida").fetchone()[0]
    ultimo = c.execute("SELECT MAX(ts) FROM lecturas").fetchone()[0]
    c.close()
    assert n1 == n2 == total and total > 0 and cola == 0
    assert ultimo < "2026-01-14T23:00"   # termina antes de la ventana NEWS2


def test_calibracion_habilita_linea_base(tmp_path):
    ruta = _csv(tmp_path, [f"{i},{70 + i % 3},0,16,98" for i in range(200)])
    dbp = str(tmp_path / "c.db")
    db.init_db(dbp)
    c = db.get_conn(dbp)
    c.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES ('T1','x','y','1990-01-01')")
    c.commit()
    calibracion.cargar("T1", ruta, dbp)
    hist = [r["valor"] for r in c.execute(
        "SELECT valor FROM lecturas WHERE indicador='frecuencia_cardiaca'")]
    c.close()
    assert engine.desviacion_linea_base(120, hist)["aviso"] is True
    assert engine.desviacion_linea_base(71, hist)["aviso"] is False
