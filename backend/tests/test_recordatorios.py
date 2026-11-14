from datetime import datetime, timedelta, timezone

import pytest

from app import config
from app.repositorios import conexion as db
from app.servicios import lecturas as servicio
from app.servicios import recordatorios as rec


@pytest.fixture()
def conn(tmp_path):
    ruta = str(tmp_path / "r.db")
    db.init_db(ruta)
    c = db.get_conn(ruta)
    for tid in ("T1", "T2", "T3"):
        c.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES (?,?,?,?)", (tid, f"N{tid}", "r", "1990-01-01"))
    c.commit()
    yield c
    c.close()


def ahora():
    return datetime.now(timezone.utc)


def test_sin_capturas_el_recordatorio_esta_vencido_y_lo_dice(conn):
    r = rec.recordatorio_tripulante(conn, "T1", ahora=ahora())
    assert r["vencido"] and r["sin_capturas"] and r["ultima_captura_ts"] is None


def test_en_verde_vence_a_los_60_minutos(conn):
    servicio.registrar_lectura(conn, "T1", "spo2", 98)
    t0 = ahora()
    antes = rec.recordatorio_tripulante(conn, "T1", ahora=t0 + timedelta(minutes=30))
    assert antes["vencido"] is False and 25 < antes["faltan_en_min"] <= 30 and antes["intervalo_min"] == 60
    despues = rec.recordatorio_tripulante(conn, "T1", ahora=t0 + timedelta(minutes=75))
    assert despues["vencido"] is True and 10 < despues["atrasado_min"] <= 15


def test_en_rojo_el_intervalo_es_mucho_mas_corto(conn):
    servicio.registrar_lectura(conn, "T1", "spo2", 88)
    r = rec.recordatorio_tripulante(conn, "T1", ahora=ahora() + timedelta(minutes=6))
    assert r["nivel_general"] == "rojo" and r["intervalo_min"] == 5 and r["vencido"] is True


def test_la_preferencia_de_recordatorios_cambia_el_intervalo_sin_alargar_emergencias(conn):
    from app.servicios import preferencias
    preferencias.guardar(conn, "T1", "directo", "completo", "frecuente")
    preferencias.guardar(conn, "T2", "directo", "completo", "minimo")
    servicio.registrar_lectura(conn, "T1", "spo2", 98)
    servicio.registrar_lectura(conn, "T2", "spo2", 98)
    servicio.registrar_lectura(conn, "T3", "spo2", 88)
    preferencias.guardar(conn, "T3", "directo", "completo", "minimo")
    t = ahora()
    assert rec.recordatorio_tripulante(conn, "T1", ahora=t)["intervalo_min"] == 30      # frecuente: la mitad
    assert rec.recordatorio_tripulante(conn, "T2", ahora=t)["intervalo_min"] == 90      # mínimo: más espaciado en verde
    assert rec.recordatorio_tripulante(conn, "T3", ahora=t)["intervalo_min"] == 5       # en rojo nunca se alarga


def test_las_series_de_calibracion_no_cuentan_como_una_captura(conn):
    conn.execute("""INSERT INTO lecturas (tripulante_id, indicador, valor, unidad, nivel, puntos_news2, origen, ts)
                    VALUES ('T1','spo2',97,'%','verde',0,'calibracion', ?)""", (ahora().isoformat(),))
    conn.commit()
    assert rec.recordatorio_tripulante(conn, "T1")["sin_capturas"] is True


def test_la_tripulacion_se_ordena_con_el_mas_atrasado_primero(conn):
    servicio.registrar_lectura(conn, "T1", "spo2", 98)          # al día
    servicio.registrar_lectura(conn, "T2", "spo2", 88)          # rojo: se vence enseguida
    r = rec.recordatorios_tripulacion(conn, ahora=ahora() + timedelta(minutes=20))
    ids = [x["tripulante_id"] for x in r["tripulacion"]]
    assert ids[0] == "T3" and ids.index("T2") < ids.index("T1")      # T3 sin capturas, luego T2 vencido, luego T1 al día
    assert r["vencidos"] == 2 and r["tripulacion"][-1]["vencido"] is False


def test_endpoints(cliente):
    cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 98})
    todos = cliente.get("/api/recordatorios").json()
    assert {t["tripulante_id"] for t in todos["tripulacion"]} == {"T1", "T2", "T3", "T4"}
    uno = cliente.get("/api/recordatorios/T1").json()
    assert uno["vencido"] is False and uno["intervalo_min"] == 60
    assert cliente.get("/api/recordatorios/X").status_code == 404


def test_con_autenticacion_exige_sesion(cliente_auth):
    assert cliente_auth.get("/api/recordatorios").status_code == 401
    assert cliente_auth.get("/api/recordatorios", headers=cliente_auth.entrar("T3")).status_code == 200
