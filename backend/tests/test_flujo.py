import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from app import config
from app.dominio import flujo as reglas
from app.repositorios import conexion as db
from app.servicios import cola, flujo


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "FLUJO_VENTANA_S", 60.0)
    monkeypatch.setattr(config, "FLUJO_ENFRIAMIENTO_S", 30.0)
    ruta = str(tmp_path / "f.db")
    db.init_db(ruta)
    c = db.get_conn(ruta)
    c.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES ('T1','x','y','1990-01-01')")
    c.commit()
    yield c
    c.close()


T0 = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)


def filas(c, ind=None):
    q = "SELECT valor, origen FROM lecturas" + (" WHERE indicador=?" if ind else "")
    return [tuple(f) for f in c.execute(q, (ind,) if ind else ()).fetchall()]


def test_es_extremo_solo_cuando_el_valor_por_si_solo_seria_rojo():
    assert reglas.es_extremo("spo2", 88) and reglas.es_extremo("frecuencia_cardiaca", 140)
    assert reglas.es_extremo("frecuencia_cardiaca", 38) and reglas.es_extremo("co2", 4.5)
    assert not reglas.es_extremo("spo2", 97) and not reglas.es_extremo("frecuencia_cardiaca", 75)
    assert not reglas.es_extremo("spo2", 93)                      # amarillo: puede esperar a la ventana
    assert reglas.es_extremo("avpu", 1) and not reglas.es_extremo("avpu", 0)


def test_la_mediana_resiste_un_artefacto_de_movimiento():
    assert reglas.resumir([72, 71, 73, 72, 250, 72, 71]) == 72.0


def test_las_muestras_se_acumulan_y_se_registra_una_sola_mediana_al_cerrar_la_ventana(conn):
    for i, v in enumerate([70, 72, 71, 73, 72]):
        r = flujo.ingresar(conn, "T1", "frecuencia_cardiaca", v, T0 + timedelta(seconds=i * 10))
        assert r["registrada"] is False and r["motivo"] == "acumulada"
    assert filas(conn) == []                                      # nada guardado todavía
    r = flujo.ingresar(conn, "T1", "frecuencia_cardiaca", 71, T0 + timedelta(seconds=60))
    assert r["registrada"] and r["motivo"] == "ventana" and r["valor_registrado"] == 71.5
    assert filas(conn) == [(71.5, "sensor")]


def test_una_banda_a_1_hz_durante_10_minutos_no_inunda_la_cola(conn):
    for s in range(600):
        flujo.ingresar(conn, "T1", "frecuencia_cardiaca", 70 + (s % 5), T0 + timedelta(seconds=s))
    eventos = conn.execute("SELECT COUNT(*) FROM cola_salida").fetchone()[0]
    assert len(filas(conn)) == eventos <= 11                      # ~una por minuto, no 600


def test_un_valor_extremo_no_espera_a_la_ventana(conn):
    r = flujo.ingresar(conn, "T1", "spo2", 88, T0)
    assert r["registrada"] and r["motivo"] == "extremo" and r["lectura"]["nivel"] == "rojo" and r["lectura"]["prioridad"] == 1
    assert conn.execute("SELECT COUNT(*) FROM cola_salida WHERE prioridad=1").fetchone()[0] == 1


def test_los_extremos_repetidos_respetan_el_enfriamiento_para_no_inundar_la_cola_en_una_crisis(conn):
    motivos = [flujo.ingresar(conn, "T1", "spo2", 88, T0 + timedelta(seconds=s))["motivo"] for s in range(0, 31, 5)]
    assert motivos.count("extremo") == 2                          # a los 0 s y de nuevo a los 30 s
    assert all(m in ("extremo", "acumulada") for m in motivos)


def test_las_ventanas_son_independientes_por_indicador_y_por_tripulante(conn):
    conn.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES ('T2','x','y','1990-01-01')")
    conn.commit()
    flujo.ingresar(conn, "T1", "frecuencia_cardiaca", 70, T0)
    flujo.ingresar(conn, "T2", "frecuencia_cardiaca", 90, T0)
    flujo.ingresar(conn, "T1", "temperatura", 36.7, T0)
    a = flujo.ingresar(conn, "T1", "frecuencia_cardiaca", 72, T0 + timedelta(seconds=60))
    assert a["valor_registrado"] == 71.0 and len(filas(conn)) == 1


def test_vaciar_cierra_las_ventanas_abiertas(conn):
    for s in range(5):
        flujo.ingresar(conn, "T1", "frecuencia_cardiaca", 70 + s, T0 + timedelta(seconds=s))
    r = flujo.vaciar(conn, "T1")
    assert r["cerradas"] == 1 and r["resultados"][0]["muestras"] == 5 and filas(conn) == [(72.0, "sensor")]
    assert flujo.vaciar(conn)["cerradas"] == 0                    # ya no queda nada abierto


def test_con_ventana_cero_cada_muestra_se_registra(conn, monkeypatch):
    monkeypatch.setattr(config, "FLUJO_VENTANA_S", 0.0)
    r = flujo.ingresar(conn, "T1", "frecuencia_cardiaca", 70, T0)
    assert r["registrada"] and r["motivo"] == "sin_agrupar"


def test_valor_invalido_se_rechaza_y_el_lote_es_todo_o_nada(conn):
    with pytest.raises(ValueError):
        flujo.ingresar(conn, "T1", "spo2", 250, T0)
    with pytest.raises(ValueError):
        flujo.ingresar_lote(conn, "T1", [("spo2", 97), ("spo2", 250)], T0)
    assert flujo._ventanas == {}                                  # no quedó ni la primera muestra


def test_endpoint_de_flujo_y_lote(cliente, monkeypatch):
    monkeypatch.setattr(config, "FLUJO_VENTANA_S", 60.0)
    r = cliente.post("/api/sensores/flujo", json={"tripulante_id": "T1", "indicador": "frecuencia_cardiaca", "valor": 72}).json()
    assert r["registrada"] is False
    lote = {"tripulante_id": "T1", "muestras": [{"indicador": "frecuencia_cardiaca", "valor": 70 + i % 3} for i in range(50)]}
    assert cliente.post("/api/sensores/flujo/lote", json=lote).json()["registradas"] == 0     # todo cabe en una ventana
    v = cliente.post("/api/sensores/flujo/vaciar", json={"tripulante_id": "T1"}).json()
    assert v["cerradas"] == 1 and v["resultados"][0]["muestras"] == 51
    assert cliente.get("/api/historial/T1?indicador=frecuencia_cardiaca").json()["puntos"][0]["origen"] == "sensor"


def test_endpoint_de_extremo_responde_de_inmediato(cliente):
    r = cliente.post("/api/sensores/flujo", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 86}).json()
    assert r["registrada"] and r["motivo"] == "extremo" and r["lectura"]["prioridad"] == 1


def test_validaciones_del_endpoint(cliente):
    assert cliente.post("/api/sensores/flujo", json={"tripulante_id": "X", "indicador": "spo2", "valor": 97}).status_code == 404
    assert cliente.post("/api/sensores/flujo", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 250}).status_code == 422
    assert cliente.post("/api/sensores/flujo/lote", json={"tripulante_id": "T1", "muestras": []}).status_code == 422
    mal = {"tripulante_id": "T1", "muestras": [{"indicador": "spo2", "valor": 97}, {"indicador": "nada", "valor": 1}]}
    assert cliente.post("/api/sensores/flujo/lote", json=mal).status_code == 422


def test_con_autenticacion_el_flujo_exige_sesion(cliente_auth):
    c = cliente_auth
    cuerpo = {"tripulante_id": "T3", "indicador": "frecuencia_cardiaca", "valor": 70}
    assert c.post("/api/sensores/flujo", json=cuerpo).status_code == 401
    assert c.post("/api/sensores/flujo", json=cuerpo, headers=c.entrar("T3")).status_code == 200
