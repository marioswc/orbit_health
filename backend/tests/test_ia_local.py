from app import config
from app.servicios import explicador_local


def test_explicacion_fallback_no_cambia_el_nivel():
    estado = {
        "nivel_general": "rojo",
        "news2": {"puntos": 3, "faltantes": ["spo2"]},
        "reglas_combinadas": [],
    }
    resultado = explicador_local.explicar(estado)
    assert resultado["fuente"] == "reglas_locales"
    assert resultado["nivel_general"] == "rojo"
    assert "modifica la alerta" in resultado["explicacion"]


def test_no_consulta_hosts_externos(monkeypatch):
    monkeypatch.setattr(config, "IA_LOCAL_URL", "https://example.com/api/generate")
    monkeypatch.setattr(config, "IA_LOCAL_MODELO", "modelo")
    resultado = explicador_local.explicar({"nivel_general": "verde"})
    assert resultado["fuente"] == "reglas_locales"


def test_endpoint_explica_estado_sin_recalcularlo(cliente):
    cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 88})
    respuesta = cliente.get("/api/estado/T1/explicacion")
    assert respuesta.status_code == 200
    assert respuesta.json()["nivel_general"] == "rojo"
