import sqlite3

from app import config


def lectura(c, ind, val, tid="T1"):
    return c.post("/api/lecturas", json={"tripulante_id": tid, "indicador": ind, "valor": val})


def test_historial_devuelve_serie_ordenada_con_resumen(cliente):
    for v in (97, 98, 96, 95):
        lectura(cliente, "spo2", v)
    h = cliente.get("/api/historial/T1?indicador=spo2").json()
    assert [p["valor"] for p in h["puntos"]] == [97, 98, 96, 95]
    assert h["resumen"] == {"n": 4, "min": 95, "max": 98, "media": 96.5} and h["unidad"] == "%"


def test_historial_respeta_limite_y_devuelve_los_mas_recientes(cliente):
    for v in range(60, 70):
        lectura(cliente, "frecuencia_cardiaca", v)
    h = cliente.get("/api/historial/T1?indicador=frecuencia_cardiaca&limite=3").json()
    assert [p["valor"] for p in h["puntos"]] == [67, 68, 69]


def test_historial_indicador_invalido_y_tripulante_inexistente(cliente):
    assert cliente.get("/api/historial/T1?indicador=inventado").status_code == 422
    assert cliente.get("/api/historial/X?indicador=spo2").status_code == 404
    assert cliente.get("/api/historial/T1?indicador=spo2").json()["puntos"] == []


def test_sueno_es_indicador_y_pocas_horas_dan_aviso_nunca_rojo(cliente):
    claves = {i["clave"] for i in cliente.get("/api/indicadores").json()}
    assert "sueno_horas" in claves
    poco = lectura(cliente, "sueno_horas", 4).json()
    assert poco["nivel"] == "amarillo" and poco["prioridad"] == 2
    assert lectura(cliente, "sueno_horas", 0).json()["nivel"] == "amarillo"
    assert lectura(cliente, "sueno_horas", 7.5, tid="T2").json()["nivel"] == "verde"
    assert lectura(cliente, "sueno_horas", 25).status_code == 422


def test_animo_es_privado_no_se_encola_y_ofrece_apoyo_si_es_bajo(cliente):
    r = cliente.post("/api/animo", json={"tripulante_id": "T1", "valor": 2}).json()
    assert r["bajo"] is True and r["capsulas"] and r["transmitido_tierra"] is False and r["privado"] is True
    assert cliente.post("/api/animo", json={"tripulante_id": "T1", "valor": 5}).json()["capsulas"] == []   # ánimo alto: sin apoyo
    assert cliente.post("/api/animo", json={"tripulante_id": "T1", "valor": 6}).status_code == 422
    assert cliente.get("/api/cola").json()["items"] == []
    conn = sqlite3.connect(config.DB_PATH)
    assert conn.execute("SELECT COUNT(*) FROM cola_salida").fetchone()[0] == 0
    conn.close()


def test_animo_normal_no_ofrece_capsulas_y_el_historial_clinico_no_lo_expone(cliente):
    assert cliente.post("/api/animo", json={"tripulante_id": "T2", "valor": 4}).json()["capsulas"] == []
    assert cliente.get("/api/historial/T2?indicador=animo").status_code == 422


def test_animo_solo_para_su_dueno_con_autenticacion(cliente_auth):
    c = cliente_auth
    h3 = c.entrar("T3")
    assert c.post("/api/animo", json={"tripulante_id": "T3", "valor": 3}, headers=h3).status_code == 200
    assert c.get("/api/animo/T3", headers=h3).json()["media"] == 3
    for otro in ("T1", "T2"):                         # ni médico ni comandante
        assert c.get("/api/animo/T3", headers=c.entrar(otro)).status_code == 403
        assert c.post("/api/animo", json={"tripulante_id": "T3", "valor": 1}, headers=c.entrar(otro)).status_code == 403
