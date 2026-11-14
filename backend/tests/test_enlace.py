import random
from datetime import timedelta

import pytest

from app import config
from app.dominio import enlace as modelo
from app.repositorios import conexion as db
from app.servicios import cola as qm


@pytest.fixture()
def conn(tmp_path):
    ruta = str(tmp_path / "t.db")
    db.init_db(ruta)
    c = db.get_conn(ruta)
    c.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES ('T1','x','y','1990-01-01')")
    c.commit()
    yield c
    c.close()


def test_perfiles_cargados():
    assert {"luna", "marte", "marte_cercano", "marte_medio"} <= set(modelo.entornos())
    assert modelo.retardo_base_s("luna") == pytest.approx(1.3)
    assert modelo.retardo_base_s("MARTE") == 1200


def test_entorno_desconocido():
    with pytest.raises(KeyError):
        modelo.retardo_base_s("jupiter")


def test_jitter_cero_es_exacto_y_con_jitter_queda_en_rango():
    assert modelo.con_jitter(100, 0) == 100
    rng = random.Random(7)
    valores = [modelo.con_jitter(100, 20, rng) for _ in range(500)]
    assert min(valores) >= 80 and max(valores) <= 120 and len(set(valores)) > 100


def test_jitter_con_semilla_es_repetible():
    a = [modelo.con_jitter(100, 10, random.Random(3)) for _ in range(3)]
    assert a[0] == a[1] == a[2]


def test_latencia_simulada_aplica_factor(monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 30.0)
    monkeypatch.setattr(config, "JITTER_PCT", 0.0)
    assert qm.latencia_s("marte") == pytest.approx(40.0)
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1.0)
    assert qm.latencia_s("marte") == pytest.approx(1200.0)   # tiempo real


def test_ida_llegada_y_confirmacion_de_vuelta(conn, monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1.0)
    monkeypatch.setattr(config, "JITTER_PCT", 0.0)
    qm.encolar(conn, "T1", "X", 1, {})
    t0 = qm._ahora()
    qm.despachar(conn, True, "marte_cercano", ahora=t0)             # 180 s de ida
    fila = qm.listar(conn, ahora=t0)[0]
    assert fila["estado"] == "en_transito" and fila["confirmado"] is False

    t1 = t0 + timedelta(seconds=181)                                  # llegó a Tierra, ACK aún en camino
    qm.actualizar_recibidos(conn, ahora=t1)
    fila = qm.listar(conn, ahora=t1)[0]
    assert fila["estado"] == "recibido" and fila["confirmado"] is False

    t2 = t0 + timedelta(seconds=361)                                  # ida y vuelta completa
    assert qm.listar(conn, ahora=t2)[0]["confirmado"] is True


def test_mismo_enlace_no_cambia_la_cadena_de_hash(conn):
    qm.encolar(conn, "T1", "X", 2, {})
    qm.despachar(conn, True, "luna")
    assert qm.verificar_cadena(conn)["valida"] is True


def test_base_antigua_se_migra_sin_perder_datos(tmp_path):
    import sqlite3
    ruta = str(tmp_path / "vieja.db")
    c = sqlite3.connect(ruta)
    c.executescript("""CREATE TABLE tripulantes (id TEXT PRIMARY KEY, nombre TEXT, rol TEXT, fecha_nacimiento DATE, creado_ts TEXT);
      CREATE TABLE cola_salida (id INTEGER PRIMARY KEY AUTOINCREMENT, tripulante_id TEXT, tipo_evento TEXT,
        prioridad INTEGER, payload TEXT, ts_guardado TEXT, hash_prev TEXT, hash TEXT UNIQUE,
        estado TEXT DEFAULT 'retenido', transmitido_ts TEXT, llegada_estimada_ts TEXT);
      INSERT INTO cola_salida (tripulante_id,tipo_evento,prioridad,payload,ts_guardado,hash_prev,hash)
        VALUES ('T1','X',1,'{}','t','G','h');""")
    c.commit(); c.close()
    db.init_db(ruta)
    c = db.get_conn(ruta)
    assert "ack_estimado_ts" in {f["name"] for f in c.execute("PRAGMA table_info(cola_salida)")}
    assert c.execute("SELECT COUNT(*) FROM cola_salida").fetchone()[0] == 1
    c.close()


def test_endpoint_de_latencia(cliente):
    r = cliente.get("/api/enlace/latencia").json()
    assert r["enlace"]["entorno"] and r["retardo_real_s"] > 0
    assert r["ida_y_vuelta_real_s"] == 2 * r["retardo_real_s"]
    assert "marte" in r["perfiles"] and r["en_transito"] == 0


def test_cambiar_a_perfil_nuevo_y_rechazar_desconocido(cliente):
    assert cliente.post("/api/enlace", json={"activo": True, "entorno": "marte_cercano"}).status_code == 200
    assert cliente.get("/api/enlace/latencia").json()["retardo_real_s"] == 180
    assert cliente.post("/api/enlace", json={"activo": True, "entorno": "jupiter"}).status_code == 422


def test_despacho_escalonado_hace_llegar_primero_prioridad_1(conn, monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1.0)
    monkeypatch.setattr(config, "JITTER_PCT", 0.0)
    qm.encolar(conn, "T1", "RUTINA", 3, {})
    qm.encolar(conn, "T1", "EMERGENCIA", 1, {})
    t0 = qm._ahora()
    qm.despachar(conn, True, "marte_cercano", ahora=t0)  # 180 s base, P1 sale en t0, P3 sale en t0 + 1 s
    t_llega_p1 = t0 + timedelta(seconds=180.2)
    qm.actualizar_recibidos(conn, ahora=t_llega_p1)
    estados = {f["prioridad"]: f["estado"] for f in qm.listar(conn, ahora=t_llega_p1)}
    assert estados[1] == "recibido" and estados[3] == "en_transito"


def test_cambio_entorno_recalcula_eventos_en_transito(conn, monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1.0)
    monkeypatch.setattr(config, "JITTER_PCT", 0.0)
    t0 = qm._ahora()
    qm.encolar(conn, "T1", "LECTURA", 1, {})
    qm.cambiar_enlace(conn, True, "marte", ahora=t0)  # 1200 s
    assert qm.listar(conn, ahora=t0 + timedelta(seconds=5))[0]["estado"] == "en_transito"
    # Al cambiar a Luna (1.3 s) tras 5 s de vuelo, ya superó el retardo lunar y pasa a recibido
    qm.cambiar_enlace(conn, True, "luna", ahora=t0 + timedelta(seconds=5))
    assert qm.listar(conn, ahora=t0 + timedelta(seconds=5))[0]["estado"] == "recibido"


def test_factor_aceleracion_cero_o_negativo_no_falla(monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 0.0)
    monkeypatch.setattr(config, "JITTER_PCT", 0.0)
    assert qm.latencia_s("marte") == pytest.approx(1200.0)
    monkeypatch.setattr(config, "FACTOR_ACELERACION", -5.0)
    assert qm.latencia_s("marte") == pytest.approx(1200.0)
