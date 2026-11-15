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


def test_el_sensor_simulado_integra_exposicion_a_radiacion(cliente):
    r = cliente.post("/api/demo/sensor/T1?perfil=exposicion_radiacion&ticks=12&semilla=7")
    assert r.status_code == 200
    rondas = r.json()["rondas"]
    dosis = [ronda["valores"]["dosis_pct"] for ronda in rondas]
    assert dosis[0] < 70 <= dosis[-1]
    assert dosis == sorted(dosis)
    assert rondas[-1]["nivel"] == "rojo"
    assert origenes() == {"simulado"}
    historial = cliente.get("/api/historial/T1?indicador=dosis_pct").json()["puntos"]
    assert len(historial) == 12 and {p["origen"] for p in historial} == {"simulado"}
    assert cliente.get("/api/cola/verificar").json()["valida"] is True


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


def test_perfiles_ampliados_cubren_reglas_combinadas_glucosa_o2_y_news2_completo(cliente):
    # 1. Proceso infeccioso: fiebre + taquicardia activa posible_proceso_infeccioso
    r_inf = cliente.post("/api/demo/sensor/T1?perfil=proceso_infeccioso&ticks=12&semilla=7").json()
    assert r_inf["rondas"][-1]["nivel"] in ("amarillo", "rojo")
    estado_t1 = cliente.get("/api/estado/T1").json()
    assert "posible_proceso_infeccioso" in {rc["id"] for rc in estado_t1["reglas_combinadas"]}
    assert estado_t1["news2"]["faltantes"] == []  # avpu se incluye en el simulador

    # 2. Intolerancia ortostática: taquicardia + hipotensión sistólica y diastólica (<60 mmHg)
    r_ort = cliente.post("/api/demo/sensor/T2?perfil=intolerancia_ortostatica&ticks=12&semilla=7").json()
    assert r_ort["rondas"][-1][" valores" if " valores" in r_ort["rondas"][-1] else "valores"]["presion_diastolica"] < 60
    estado_t2 = cliente.get("/api/estado/T2").json()
    assert "posible_intolerancia_ortostatica" in {rc["id"] for rc in estado_t2["reglas_combinadas"]}

    # 3. Hipoglucemia: glucosa cae de rango normal (<100) a amarillo (<70) y rojo (<54)
    r_glu = cliente.post("/api/demo/sensor/T3?perfil=hipoglucemia&ticks=12&semilla=7").json()
    glucosas = [ronda["valores"]["glucosa"] for ronda in r_glu["rondas"]]
    assert glucosas[0] >= 70 and glucosas[-1] < 54
    assert r_glu["rondas"][-1]["nivel"] == "rojo"

    # 4. Hipoxia ambiental por caída de O2 en cabina (<19.0 % es rojo)
    r_o2 = cliente.post("/api/demo/sensor/T4?perfil=hipoxia_ambiental_o2&ticks=12&semilla=7").json()
    o2_vals = [ronda["valores"]["o2_cabina"] for ronda in r_o2["rondas"]]
    assert o2_vals[0] > 19.5 and o2_vals[-1] < 19.0
    assert r_o2["rondas"][-1]["nivel"] == "rojo"


def test_realismo_fisiologico_acoplamiento_y_filtro_de_mediana_ante_artefactos(cliente):
    from app.repositorios.conexion import get_conn
    serie_con_artefacto = d.generar("estable", 7, semilla=7, artefactos=True)
    assert serie_con_artefacto[3]["frecuencia_cardiaca"] == 124.0
    assert serie_con_artefacto[3]["frecuencia_respiratoria"] == 23.0

    conn = get_conn()
    try:
        res = d.simular_ventana_con_artefacto(conn, tid="T1", muestras=7, semilla=7)
    finally:
        conn.close()
    assert res["pico_artefacto_fc"] == 124.0
    assert res["promedio_sin_filtro"] > 75.0      # el promedio simple se contamina por el golpe de muñeca
    assert res["mediana_registrada"] <= 72.0      # la mediana filtra el artefacto y conserva el valor real
    assert res["nivel_registrado"] == "verde"
