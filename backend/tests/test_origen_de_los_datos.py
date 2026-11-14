"""Un dato inventado nunca debe pasar por real: el origen se guarda, viaja a Tierra y aparece en el historial."""
import json
import sqlite3

import pytest

from app import config


def origenes():
    c = sqlite3.connect(config.DB_PATH)
    r = {f[0] for f in c.execute("SELECT DISTINCT origen FROM lecturas")}
    c.close()
    return r


def payload_origen():
    c = sqlite3.connect(config.DB_PATH)
    r = {json.loads(f[0]).get("origen") for f in c.execute("SELECT payload FROM cola_salida")}
    c.close()
    return r


def test_una_fuente_simulada_puede_declararse_y_se_guarda_como_simulado(cliente):
    r = cliente.post("/api/sensores/lectura", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 97, "origen": "simulado"})
    assert r.status_code == 200 and origenes() == {"simulado"}


def test_un_dispositivo_real_sigue_siendo_sensor_por_defecto(cliente):
    cliente.post("/api/sensores/lectura", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 97})
    cliente.post("/api/sensores/lote", json={"tripulante_id": "T1", "lecturas": [{"indicador": "temperatura", "valor": 36.8}]})
    assert origenes() == {"sensor"}


def test_la_captura_manual_sigue_siendo_manual(cliente):
    cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 97})
    assert origenes() == {"manual"}


def test_no_se_acepta_un_origen_inventado_ni_calibracion_ni_manual_por_la_via_de_sensores(cliente):
    for origen in ("calibracion", "manual", "real", ""):
        r = cliente.post("/api/sensores/lectura", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 97, "origen": origen})
        assert r.status_code == 422, origen
    assert origenes() == set()


def test_el_flujo_conserva_el_origen_de_sus_muestras_al_cerrar_la_ventana(cliente):
    cuerpo = {"tripulante_id": "T1", "origen": "simulado", "muestras": [{"indicador": "frecuencia_cardiaca", "valor": 70 + i} for i in range(5)]}
    assert cliente.post("/api/sensores/flujo/lote", json=cuerpo).status_code == 200
    cliente.post("/api/sensores/flujo/vaciar", json={"tripulante_id": "T1"})
    assert origenes() == {"simulado"}


def test_el_extremo_del_flujo_tambien_conserva_el_origen(cliente):
    cliente.post("/api/sensores/flujo", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 86, "origen": "simulado"})
    assert origenes() == {"simulado"}


def test_el_evento_que_viaja_a_tierra_dice_de_donde_viene_el_dato(cliente, monkeypatch):
    monkeypatch.setattr(config, "FACTOR_ACELERACION", 1e9)
    cliente.post("/api/sensores/lectura", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 88, "origen": "simulado"})
    cliente.post("/api/sensores/lectura", json={"tripulante_id": "T2", "indicador": "spo2", "valor": 88})
    cliente.post("/api/lecturas", json={"tripulante_id": "T3", "indicador": "spo2", "valor": 88})
    assert payload_origen() == {"simulado", "sensor", "manual"}
    visto = {m["payload"]["origen"] for m in cliente.get("/api/tierra/mensajes").json()["recibidos"]}
    assert visto == {"simulado", "sensor", "manual"}


@pytest.mark.parametrize("escenario", ["hipoxia_eclipse", "co2_colectivo"])
def test_los_escenarios_guionizados_se_declaran_simulados(cliente, escenario):
    cliente.post(f"/api/demo/escenarios/{escenario}")
    assert origenes() == {"simulado"}


def test_el_historial_y_el_informe_muestran_el_origen(cliente):
    cliente.post("/api/demo/sensor/T1?perfil=estable&ticks=3")
    h = cliente.get("/api/historial/T1?indicador=spo2").json()["puntos"]
    assert h and {p["origen"] for p in h} == {"simulado"}
    assert {x["origen"] for x in cliente.get("/api/informe/T1").json()["lecturas_recientes"]} == {"simulado"}
