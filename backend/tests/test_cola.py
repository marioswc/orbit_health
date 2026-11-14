import pytest

from app import db, queue_manager as qm


@pytest.fixture()
def conn(tmp_path):
    ruta = str(tmp_path / "t.db")
    db.init_db(ruta)
    c = db.get_conn(ruta)
    c.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES ('T1','Prueba','Rol','1990-01-01')")
    c.commit()
    yield c
    c.close()


def test_eclipse_retiene_y_reconexion_prioriza(conn):
    qm.encolar(conn, "T1", "LECTURA", 3, {"n": 1})
    qm.encolar(conn, "T1", "LECTURA", 2, {"n": 2})
    qm.encolar(conn, "T1", "LECTURA", 1, {"n": 3})
    assert qm.despachar(conn, enlace_activo=False) == []
    assert conn.execute("SELECT COUNT(*) FROM cola_salida WHERE estado='retenido'").fetchone()[0] == 3
    salida = qm.despachar(conn, enlace_activo=True)
    assert [m["prioridad"] for m in salida] == [1, 2, 3]


def test_misma_prioridad_por_antiguedad(conn):
    a = qm.encolar(conn, "T1", "X", 1, {})
    b = qm.encolar(conn, "T1", "X", 1, {})
    assert [m["id"] for m in qm.despachar(conn, True)] == [a, b]


def test_cadena_valida_y_detecta_manipulacion(conn):
    for i in range(3):
        qm.encolar(conn, "T1", "X", 2, {"i": i})
    assert qm.verificar_cadena(conn)["valida"] is True
    conn.execute("UPDATE cola_salida SET payload='{\"i\":99}' WHERE id=2")
    conn.commit()
    r = qm.verificar_cadena(conn)
    assert r["valida"] is False and r["primer_invalido"] == 2


def test_recibido_tras_latencia(conn):
    from datetime import timedelta
    qm.encolar(conn, "T1", "X", 1, {})
    qm.despachar(conn, True, "marte")
    assert qm.actualizar_recibidos(conn) == 0
    futuro = qm._ahora() + timedelta(seconds=3600)
    assert qm.actualizar_recibidos(conn, futuro) == 1
    # estado no afecta la cadena
    assert qm.verificar_cadena(conn)["valida"] is True


def test_integridad_pura_sin_base_de_datos():
    from app.dominio import integridad as i
    h1 = i.calcular_hash(i.GENESIS, "T1", "X", 1, "{}", "t1")
    h2 = i.calcular_hash(h1, "T1", "X", 2, "{}", "t2")
    filas = [
        {"id": 1, "tripulante_id": "T1", "tipo_evento": "X", "prioridad": 1, "payload": "{}", "ts_guardado": "t1", "hash_prev": i.GENESIS, "hash": h1},
        {"id": 2, "tripulante_id": "T1", "tipo_evento": "X", "prioridad": 2, "payload": "{}", "ts_guardado": "t2", "hash_prev": h1, "hash": h2},
    ]
    assert i.verificar_filas(filas)["valida"] is True
    filas[1]["prioridad"] = 3
    assert i.verificar_filas(filas) == {"valida": False, "total": 2, "primer_invalido": 2}
