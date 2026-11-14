import sqlite3

import pytest

from app import config
from app.dominio.catalogos import validar
from app.fuentes import dispositivo_simulado as d


def origenes():
    c = sqlite3.connect(config.DB_PATH)
    r = {f[0] for f in c.execute("SELECT DISTINCT origen FROM lecturas")}
    c.close()
    return r


def test_misma_semilla_misma_serie_y_semilla_distinta_difiere():
    assert d.generar("deterioro_respiratorio", 10, 5) == d.generar("deterioro_respiratorio", 10, 5)
    assert d.generar("deterioro_respiratorio", 10, 5) != d.generar("deterioro_respiratorio", 10, 6)


def test_todos_los_valores_generados_son_validos_para_el_catalogo():
    for perfil in d.PERFILES:
        for tick in d.generar(perfil, 60, 1):
            for indicador, valor in tick.items():
                assert validar(indicador, valor) is None, (perfil, indicador, valor)


def test_el_perfil_estable_no_sale_de_su_rango_normal():
    from app.dominio import reglas
    for tick in d.generar("estable", 60, 3):
        r = reglas.evaluar_news2({**tick, "avpu": "A"})
        assert r.nivel == "verde" and r.puntos == 0, tick


def test_el_deterioro_pasa_por_amarillo_antes_de_rojo(cliente):
    r = cliente.post("/api/demo/sensor/T1?perfil=deterioro_respiratorio&ticks=15&semilla=7").json()
    assert r["primera_ronda_rojo"] is not None
    assert r["primera_ronda_amarillo"] is None or r["primera_ronda_amarillo"] <= r["primera_ronda_rojo"]
    assert r["rondas"][0]["nivel"] == "verde" and r["rondas"][-1]["nivel"] == "rojo"
    assert origenes() == {"simulado"}                                          # lo inventado se declara simulado, nunca sensor


def test_la_lectura_de_sensor_usa_la_misma_clasificacion_y_cola_con_origen_sensor(cliente):
    r = cliente.post("/api/sensores/lectura", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 88, "dispositivo_id": "reloj-1"}).json()
    assert r["nivel"] == "rojo" and r["prioridad"] == 1 and r["acciones_sugeridas"]
    assert origenes() == {"sensor"}
    cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 98})
    assert origenes() == {"sensor", "manual"}                         # la captura manual sigue siendo manual
    assert cliente.get("/api/historial/T1?indicador=spo2").json()["puntos"][0]["origen"] == "sensor"


def test_el_lote_guarda_todo_y_resume_el_peor_nivel(cliente):
    lote = {"tripulante_id": "T1", "dispositivo_id": "reloj-1", "lecturas": [
        {"indicador": "frecuencia_cardiaca", "valor": 70}, {"indicador": "spo2", "valor": 97}, {"indicador": "temperatura", "valor": 36.8}]}
    r = cliente.post("/api/sensores/lote", json=lote).json()
    assert r["guardadas"] == 3 and r["peor_nivel"] == "verde" and r["dispositivo_id"] == "reloj-1"


def test_el_lote_es_todo_o_nada(cliente):
    lote = {"tripulante_id": "T1", "lecturas": [{"indicador": "spo2", "valor": 97}, {"indicador": "spo2", "valor": 250}]}
    r = cliente.post("/api/sensores/lote", json=lote)
    assert r.status_code == 422 and "Lectura 2" in r.json()["detail"]
    assert cliente.get("/api/historial/T1?indicador=spo2").json()["puntos"] == []       # no se guardó ni la primera


def test_limites_del_lote_y_datos_invalidos(cliente):
    assert cliente.post("/api/sensores/lote", json={"tripulante_id": "T1", "lecturas": []}).status_code == 422
    muchas = [{"indicador": "spo2", "valor": 97}] * 101
    assert cliente.post("/api/sensores/lote", json={"tripulante_id": "T1", "lecturas": muchas}).status_code == 422
    assert cliente.post("/api/sensores/lectura", json={"tripulante_id": "X", "indicador": "spo2", "valor": 97}).status_code == 404
    assert cliente.post("/api/sensores/lectura", json={"tripulante_id": "T1", "indicador": "nada", "valor": 1}).status_code == 422


def test_perfil_o_ticks_invalidos_en_la_demo(cliente):
    assert cliente.post("/api/demo/sensor/T1?perfil=raro").status_code == 422
    assert cliente.post("/api/demo/sensor/T1?ticks=0").status_code == 422
    assert cliente.post("/api/demo/sensor/X").status_code == 404


def test_con_autenticacion_los_sensores_exigen_sesion_y_la_demo_un_rol(cliente_auth):
    c = cliente_auth
    cuerpo = {"tripulante_id": "T1", "indicador": "spo2", "valor": 97}
    assert c.post("/api/sensores/lectura", json=cuerpo).status_code == 401
    assert c.post("/api/sensores/lectura", json=cuerpo, headers=c.entrar("T3")).status_code == 200
    assert c.post("/api/demo/sensor/T1", headers=c.entrar("T3")).status_code == 403
    assert c.post("/api/demo/sensor/T1?ticks=3", headers=c.entrar("T2")).status_code == 200
