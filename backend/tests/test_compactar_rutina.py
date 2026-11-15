import sqlite3

from app import config
from app.servicios import cola


def _eventos(conn, tid, tipo, prioridad, n):
    conn.execute("BEGIN IMMEDIATE")
    for i in range(n):
        cola.encolar_sin_commit(conn, tid, tipo, prioridad, {"i": i})
    conn.commit()


def _conn():
    c = sqlite3.connect(config.DB_PATH); c.row_factory = sqlite3.Row
    return c


def test_tras_un_apagon_la_rutina_sale_resumida_y_lo_urgente_intacto(cliente, monkeypatch):
    monkeypatch.setattr(config, "COMPACTAR_RUTINA_DESDE", 10)
    c = _conn()
    _eventos(c, "T1", "lectura", 3, 12)
    _eventos(c, "T2", "lectura", 3, 5)
    _eventos(c, "T1", "alerta", 1, 2)
    _eventos(c, "T2", "aviso", 2, 3)
    salida = cola.despachar(c, True, "marte")
    por_tipo = {}
    for f in salida:
        por_tipo[f["tipo_evento"]] = por_tipo.get(f["tipo_evento"], 0) + 1
    assert por_tipo == {"alerta": 2, "aviso": 3, "resumen_rutina": 2}               # un resumen por tripulante con rutina
    assert salida[0]["prioridad"] == 1                                               # lo urgente sale primero
    assert c.execute("SELECT COUNT(*) FROM cola_salida WHERE resumido=1").fetchone()[0] == 17
    resumen = c.execute("SELECT payload FROM cola_salida WHERE tipo_evento='resumen_rutina' AND tripulante_id='T1'").fetchone()[0]
    assert '"cantidad":12' in resumen
    assert cola.verificar_cadena(c)["valida"] is True                               # nada se borró: la cadena sigue íntegra
    assert c.execute("SELECT COUNT(*) FROM cola_salida").fetchone()[0] == 17 + 5 + 2   # originales + 2 resúmenes
    c.close()


def test_por_debajo_del_umbral_no_se_resume(cliente, monkeypatch):
    monkeypatch.setattr(config, "COMPACTAR_RUTINA_DESDE", 20)
    c = _conn()
    _eventos(c, "T1", "lectura", 3, 5)
    salida = cola.despachar(c, True, "marte")
    assert len(salida) == 5 and all(f["tipo_evento"] == "lectura" for f in salida)
    c.close()


def test_con_umbral_cero_nunca_resume(cliente, monkeypatch):
    monkeypatch.setattr(config, "COMPACTAR_RUTINA_DESDE", 0)
    c = _conn()
    _eventos(c, "T1", "lectura", 3, 30)
    assert len(cola.despachar(c, True, "marte")) == 30
    c.close()


def test_sin_enlace_no_se_resume_nada(cliente, monkeypatch):
    monkeypatch.setattr(config, "COMPACTAR_RUTINA_DESDE", 5)
    c = _conn()
    _eventos(c, "T1", "lectura", 3, 30)
    assert cola.despachar(c, False, "marte") == []
    assert c.execute("SELECT COUNT(*) FROM cola_salida WHERE resumido=1").fetchone()[0] == 0
    c.close()
