import sqlite3
from datetime import timedelta

import pytest

from app import config
from app.repositorios import conexion as db
from app.servicios import cola as qm


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "JITTER_PCT", 0.0)
    ruta = str(tmp_path / "t.db")
    db.init_db(ruta)
    c = db.get_conn(ruta)
    c.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES ('T1','x','y','1990-01-01')")
    c.commit()
    yield c
    c.close()


def lectura(c, ind, val, tid="T1"):
    return c.post("/api/lecturas", json={"tripulante_id": tid, "indicador": ind, "valor": val})


def test_nada_llega_antes_de_su_hora_y_todo_llega_despues(conn, monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1.0)
    qm.encolar(conn, "T1", "X", 1, {"a": 1})
    t0 = qm._ahora()
    qm.despachar(conn, True, "marte_cercano", ahora=t0)                         # 180 s de ida
    assert qm.vista_tierra(conn, ahora=t0 + timedelta(seconds=179))["recibidos"] == []
    v = qm.vista_tierra(conn, ahora=t0 + timedelta(seconds=181))
    assert len(v["recibidos"]) == 1 and v["en_camino"] == 0 and v["recibidos"][0]["payload"] == {"a": 1}


def test_lo_que_aun_viaja_se_cuenta_como_en_camino(conn, monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1.0)
    qm.encolar(conn, "T1", "X", 2, {})
    t0 = qm._ahora()
    qm.despachar(conn, True, "marte", ahora=t0)
    v = qm.vista_tierra(conn, ahora=t0 + timedelta(seconds=10))
    assert v["recibidos"] == [] and v["en_camino"] == 1


def test_lo_retenido_en_eclipse_no_llega_a_tierra(conn):
    qm.encolar(conn, "T1", "X", 1, {})
    v = qm.vista_tierra(conn, ahora=qm._ahora() + timedelta(days=1))
    assert v["recibidos"] == [] and v["retenidos_a_bordo"] == 1


def test_la_urgencia_sale_primero_y_luego_por_orden(conn, monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1e9)
    for prio in (3, 1, 2, 1):
        qm.encolar(conn, "T1", f"P{prio}", prio, {})
    qm.despachar(conn, True, "luna")
    v = qm.vista_tierra(conn, ahora=qm._ahora() + timedelta(seconds=5))
    assert [m["prioridad"] for m in v["recibidos"]] == [1, 1, 2, 3]
    assert v["recibidos"][0]["id"] < v["recibidos"][1]["id"]


def test_es_de_solo_lectura_e_idempotente(conn, monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1e9)
    qm.encolar(conn, "T1", "X", 1, {})
    qm.despachar(conn, True, "luna")
    futuro = qm._ahora() + timedelta(seconds=5)
    a = qm.vista_tierra(conn, ahora=futuro)
    b = qm.vista_tierra(conn, ahora=futuro)
    assert a == b and len(a["recibidos"]) == 1                                  # leer dos veces no reparte ni consume
    assert conn.execute("SELECT estado FROM cola_salida").fetchone()[0] == "en_transito"   # y no cambió el estado


def test_endpoint_muestra_lo_que_llego_sin_consumirlo(cliente, monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1e9)
    lectura(cliente, "spo2", 88)
    r1 = cliente.get("/api/tierra/mensajes").json()
    r2 = cliente.get("/api/tierra/mensajes").json()
    assert len(r1["recibidos"]) == len(r2["recibidos"]) == 1
    m = r1["recibidos"][0]
    assert m["prioridad"] == 1 and m["payload"]["indicador"] == "spo2" and m["payload"]["reglas_version"]


def test_en_eclipse_el_endpoint_no_ve_nada_hasta_reconectar(cliente, monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1e9)
    cliente.post("/api/enlace", json={"activo": False, "entorno": "marte"})
    lectura(cliente, "spo2", 88)
    assert cliente.get("/api/tierra/mensajes").json()["recibidos"] == []
    assert cliente.get("/api/tierra/mensajes").json()["retenidos_a_bordo"] == 1
    cliente.post("/api/enlace", json={"activo": True, "entorno": "marte"})
    assert len(cliente.get("/api/tierra/mensajes").json()["recibidos"]) == 1


def test_lo_privado_nunca_aparece_en_la_vista_de_tierra(cliente, monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1e9)
    cliente.post("/api/diario", json={"tripulante_id": "T1", "contenido": "secreto XYZ"})
    cliente.post("/api/animo", json={"tripulante_id": "T1", "valor": 1})
    cliente.post("/api/tamizajes", json={"tripulante_id": "T1", "item1": 3, "item2": 3})
    lectura(cliente, "spo2", 97)
    texto = cliente.get("/api/tierra/mensajes").text
    assert "XYZ" not in texto and "animo" not in texto and "tamizaje" not in texto.lower()


def test_con_autenticacion_exige_sesion(cliente_auth):
    assert cliente_auth.get("/api/tierra/mensajes").status_code == 401
    assert cliente_auth.get("/api/tierra/mensajes", headers=cliente_auth.entrar("T3")).status_code == 200


def test_el_indice_por_llegada_existe_tambien_en_bases_ya_creadas(tmp_path):
    ruta = str(tmp_path / "vieja.db")
    c = sqlite3.connect(ruta)
    c.executescript("""CREATE TABLE tripulantes (id TEXT PRIMARY KEY, nombre TEXT, rol TEXT, fecha_nacimiento DATE, creado_ts TEXT);
      CREATE TABLE cola_salida (id INTEGER PRIMARY KEY AUTOINCREMENT, tripulante_id TEXT, tipo_evento TEXT, prioridad INTEGER,
        payload TEXT, ts_guardado TEXT, hash_prev TEXT, hash TEXT UNIQUE, estado TEXT DEFAULT 'retenido',
        transmitido_ts TEXT, llegada_estimada_ts TEXT);""")
    c.commit(); c.close()
    db.init_db(ruta)
    c = db.get_conn(ruta)
    nombres = {f["name"] for f in c.execute("PRAGMA index_list(cola_salida)")}
    c.close()
    assert "idx_cola_llegada" in nombres
