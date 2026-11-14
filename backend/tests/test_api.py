import pytest
import sqlite3

from app import config

NORMAL = {"frecuencia_respiratoria": 16, "spo2": 98, "presion_sistolica": 120,
          "frecuencia_cardiaca": 70, "temperatura": 36.8}


def lectura(c, ind, val, tid="T1"):
    return c.post("/api/lecturas", json={"tripulante_id": tid, "indicador": ind, "valor": val})


def test_lectura_normal_verde_prioridad_3(cliente):
    r = lectura(cliente, "spo2", 98).json()
    assert r["nivel"] == "verde" and r["prioridad"] == 3


def test_hipoxia_severa_roja_prioridad_1(cliente):
    r = lectura(cliente, "spo2", 90).json()
    assert r["nivel"] == "rojo" and r["prioridad"] == 1


def test_news2_combina_lecturas_recientes(cliente):
    for k, v in NORMAL.items():
        lectura(cliente, k, v)
    r = lectura(cliente, "spo2", 92).json()
    assert r["puntos_news2"] == 2 and r["nivel"] == "verde"


def test_rango_invalido_422(cliente):
    assert lectura(cliente, "spo2", 150).status_code == 422
    assert lectura(cliente, "inventado", 1).status_code == 422


def test_tripulante_inexistente_404(cliente):
    assert lectura(cliente, "spo2", 98, tid="X").status_code == 404


def test_diario_no_encola(cliente):
    r = cliente.post("/api/diario", json={"tripulante_id": "T1", "contenido": "nota"}).json()
    assert r["transmitido_tierra"] is False
    conn = sqlite3.connect(config.DB_PATH)
    assert conn.execute("SELECT COUNT(*) FROM cola_salida").fetchone()[0] == 0
    conn.close()


def test_tamizaje_positivo_no_encola_y_da_capsulas(cliente):
    r = cliente.post("/api/tamizajes", json={"tripulante_id": "T1", "item1": 2, "item2": 1}).json()
    assert r["positivo"] and r["capsulas"] and r["transmitido_tierra"] is False
    assert cliente.get("/api/cola").json()["items"] == []


def test_eclipse_y_reconexion_prioriza_rojo(cliente):
    cliente.post("/api/enlace", json={"activo": False, "entorno": "marte"})
    lectura(cliente, "temperatura", 36.8)       # verde
    lectura(cliente, "spo2", 90)                # rojo
    cola = cliente.get("/api/cola").json()
    assert cola["resumen"]["retenido"]["1"] == 1 and cola["resumen"]["retenido"]["3"] == 1
    r = cliente.post("/api/enlace", json={"activo": True, "entorno": "marte"}).json()
    assert [m["prioridad"] for m in r["despachados"]] == [1, 3]
    assert cliente.get("/api/cola/verificar").json()["valida"] is True


def test_respuesta_incluye_proxima_captura(cliente):
    assert lectura(cliente, "spo2", 98).json()["proxima_captura_min"] == 60
    assert lectura(cliente, "spo2", 90).json()["proxima_captura_min"] == 5
    assert cliente.get("/api/estado/T1").json()["proxima_captura_min"] == 5


def test_umbrales_expone_estado_de_validacion(cliente):
    r = cliente.get("/api/umbrales").json()
    assert r["estado"].startswith("pendiente") and r["version"]


def test_estado_resumen(cliente):
    lectura(cliente, "spo2", 90)
    e = cliente.get("/api/estado/T1").json()
    assert e["nivel_general"] == "rojo" and e["indicadores"][0]["indicador"] == "spo2"


def test_enlace_persiste_entre_reinicios(cliente):
    from fastapi.testclient import TestClient
    from app import main
    cliente.post("/api/enlace", json={"activo": False, "entorno": "luna"})
    with TestClient(main.app) as otro:   # nuevo arranque sobre la misma base
        assert otro.get("/api/enlace").json() == {"activo": False, "entorno": "luna"}


def test_ruta_db_por_defecto_apunta_a_data_del_repo(monkeypatch):
    import importlib
    from pathlib import Path
    from app import config
    monkeypatch.delenv("ORBIT_DB_PATH", raising=False)
    try:
        importlib.reload(config)
        raiz = Path(__file__).resolve().parents[2]
        assert Path(config.DB_PATH) == raiz / "data" / "orbit_health.db"
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_ruta_db_por_defecto_es_absoluta(monkeypatch):
    import importlib
    from pathlib import Path
    from app import config
    monkeypatch.delenv("ORBIT_DB_PATH", raising=False)
    try:
        importlib.reload(config)
        assert Path(config.DB_PATH).is_absolute()
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_lectura_y_evento_son_atomicos(cliente, monkeypatch):
    """Si falla el encolado, tampoco debe quedar la lectura."""
    import sqlite3
    from app.servicios import cola

    def falla(*_a, **_k):
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(cola, "encolar_sin_commit", falla)
    with pytest.raises(RuntimeError):
        lectura(cliente, "spo2", 98)
    conn = sqlite3.connect(config.DB_PATH)
    assert conn.execute("SELECT COUNT(*) FROM lecturas").fetchone()[0] == 0
    conn.close()


def test_regla_combinada_sube_el_nivel_y_se_informa(cliente):
    lectura(cliente, "presion_sistolica", 108)
    r = lectura(cliente, "frecuencia_cardiaca", 95).json()
    assert [a["id"] for a in r["reglas_combinadas"]] == ["posible_intolerancia_ortostatica"]
    assert r["nivel"] == "amarillo" and r["prioridad"] == 2
    e = cliente.get("/api/estado/T1").json()
    assert e["nivel_general"] == "amarillo" and e["reglas_combinadas"]


def test_sin_dato_de_ambas_variables_no_hay_regla(cliente):
    r = lectura(cliente, "frecuencia_cardiaca", 95).json()
    assert r["reglas_combinadas"] == [] and r["nivel"] == "verde"


def test_alerta_colectiva_co2_con_dos_tripulantes_afectados(cliente):
    assert cliente.get("/api/alertas/colectivas").json()["alertas"] == []
    lectura(cliente, "co2", 3.6, tid="T3")                    # ambiental: no cuenta como afectado
    lectura(cliente, "spo2", 90, tid="T1")                    # rojo
    assert cliente.get("/api/alertas/colectivas").json()["alertas"] == []   # solo 1 afectado
    lectura(cliente, "spo2", 92, tid="T2")
    lectura(cliente, "frecuencia_respiratoria", 26, tid="T2")  # rojo
    r = cliente.get("/api/alertas/colectivas").json()
    assert r["alertas"] and r["alertas"][0]["id"] == "alerta_ambiental_colectiva"
    assert r["alertas"][0]["afectados"] == 2
    assert r["alertas"][0]["nivel"] == "rojo"


def test_enlace_activo_despacha_al_registrar_lectura(cliente):
    lectura(cliente, "spo2", 98)
    cola = cliente.get("/api/cola").json()
    assert cola["items"][0]["estado"] in ("en_transito", "recibido")


def test_lectura_normal_no_queda_contaminada_por_alerta_previa(cliente):
    lectura(cliente, "spo2", 88)          # rojo
    lectura(cliente, "temperatura", 36.8) # normal: debe guardarse como verde
    estado_Durante = cliente.get("/api/estado/T1").json()
    niveles = {i["indicador"]: i["nivel"] for i in estado_Durante["indicadores"]}
    assert niveles["spo2"] == "rojo" and niveles["temperatura"] == "verde"
    assert estado_Durante["nivel_general"] == "rojo"

    lectura(cliente, "spo2", 98)          # se normaliza SpO2
    estado_final = cliente.get("/api/estado/T1").json()
    assert estado_final["nivel_general"] == "verde" and estado_final["news2"]["nivel"] == "verde"


def test_estado_expone_linea_base_por_indicador(cliente):
    for v in (70, 72, 68, 71, 69, 70):
        lectura(cliente, "frecuencia_cardiaca", v)
    lectura(cliente, "frecuencia_cardiaca", 120)
    ind = {i["indicador"]: i for i in cliente.get("/api/estado/T1").json()["indicadores"]}
    lb = ind["frecuencia_cardiaca"]["linea_base"]
    assert lb["aplica"] is True and lb["n"] == 6
    assert 69 <= lb["media"] <= 71 and lb["aviso"] is True and lb["z"] > 2


def test_linea_base_sin_historial_suficiente_no_aplica(cliente):
    lectura(cliente, "spo2", 97)
    ind = cliente.get("/api/estado/T1").json()["indicadores"][0]
    assert ind["linea_base"]["aplica"] is False and ind["linea_base"]["aviso"] is False
