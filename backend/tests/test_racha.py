from datetime import datetime, timedelta, timezone

import pytest

from app.repositorios import conexion as db
from app.repositorios import lecturas as repo
from app.servicios import racha as r

HOY = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)


@pytest.fixture()
def conn(tmp_path):
    ruta = str(tmp_path / "r.db")
    db.init_db(ruta)
    c = db.get_conn(ruta)
    c.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES ('T1','x','y','1990-01-01')")
    c.commit()
    yield c
    c.close()


def dia_completo(c, dias_atras, origen="sensor", faltan=()):
    ts = (HOY - timedelta(days=dias_atras)).isoformat()
    for ind in r.VITALES_DEL_DIA:
        if ind not in faltan:
            repo.insertar(c, "T1", ind, 70.0, "u", "verde", 0, ts, origen)
    c.commit()


def test_sin_datos_no_hay_racha_ni_logros(conn):
    x = r.racha(conn, "T1", HOY)
    assert x["racha_dias"] == 0 and x["mejor_racha_dias"] == 0 and not x["hoy_completo"]
    assert not any(l["logrado"] for l in x["logros"]) and len(x["hoy_faltan"]) == 5


def test_tres_dias_seguidos_hasta_hoy_dan_racha_3_y_sus_logros(conn):
    for d in (0, 1, 2):
        dia_completo(conn, d)
    x = r.racha(conn, "T1", HOY)
    assert x["racha_dias"] == 3 and x["hoy_completo"] and x["hoy_faltan"] == []
    assert {l["id"]: l["logrado"] for l in x["logros"]} == {"primer_dia": True, "tres_dias": True, "semana": False}


def test_la_racha_no_se_rompe_porque_hoy_todavia_no_este_completo(conn):
    for d in (1, 2, 3):
        dia_completo(conn, d)
    x = r.racha(conn, "T1", HOY)
    assert x["racha_dias"] == 3 and x["hoy_completo"] is False          # cuenta desde ayer; hoy sigue en curso


def test_un_dia_sin_registro_corta_la_racha_y_se_conserva_la_mejor(conn):
    for d in (0, 1):
        dia_completo(conn, d)                                            # racha actual de 2
    for d in (3, 4, 5, 6):
        dia_completo(conn, d)                                            # el día 2 falta; antes hubo 4 seguidos
    x = r.racha(conn, "T1", HOY)
    assert x["racha_dias"] == 2 and x["mejor_racha_dias"] == 4 and x["dias_completos"] == 6


def test_un_dia_con_signos_incompletos_no_cuenta_y_dice_cuales_faltan(conn):
    dia_completo(conn, 0, faltan=("temperatura", "spo2"))
    x = r.racha(conn, "T1", HOY)
    assert x["racha_dias"] == 0 and not x["hoy_completo"]
    assert sorted(x["hoy_faltan"]) == sorted(["Temperatura", "SpO₂"])


def test_una_semana_completa_desbloquea_todos_los_logros(conn):
    for d in range(7):
        dia_completo(conn, d)
    assert all(l["logrado"] for l in r.racha(conn, "T1", HOY)["logros"])


def test_la_calibracion_no_cuenta_como_dias_de_medicion(conn):
    for d in range(5):
        dia_completo(conn, d, origen="calibracion")
    assert r.racha(conn, "T1", HOY)["dias_completos"] == 0


def test_cuenta_igual_la_captura_manual_y_la_de_sensor(conn):
    dia_completo(conn, 0, origen="manual")
    dia_completo(conn, 1, origen="sensor")
    assert r.racha(conn, "T1", HOY)["racha_dias"] == 2


def test_endpoint_y_sin_presion(cliente):
    for ind, v in (("frecuencia_respiratoria", 16), ("spo2", 98), ("presion_sistolica", 120), ("frecuencia_cardiaca", 70), ("temperatura", 36.8)):
        cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": ind, "valor": v})
    x = cliente.get("/api/racha/T1").json()
    assert x["racha_dias"] == 1 and x["hoy_completo"] and x["logros"][0]["logrado"] is True
    assert "no se rompe" in x["regla"]
    assert cliente.get("/api/racha/X").status_code == 404


def test_con_autenticacion_exige_sesion(cliente_auth):
    assert cliente_auth.get("/api/racha/T1").status_code == 401
    assert cliente_auth.get("/api/racha/T1", headers=cliente_auth.entrar("T3")).status_code == 200
