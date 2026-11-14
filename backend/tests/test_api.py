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


def test_ruta_db_por_defecto_es_absoluta():
    from pathlib import Path
    from app import config
    assert Path(config.RAIZ.parent / "data").is_absolute()
