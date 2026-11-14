from app import config
from app.servicios import voz_local


def test_endpoint_de_voz_esta_desactivado_por_defecto(cliente):
    respuesta = cliente.post("/api/voz/chat/T1", content=b"audio", headers={"Content-Type": "audio/wav"})
    assert respuesta.status_code == 503


def test_respuesta_de_voz_no_decide_el_nivel(monkeypatch):
    monkeypatch.setattr(config, "IA_LOCAL_URL", "")
    monkeypatch.setattr(config, "IA_LOCAL_MODELO", "")
    resultado = voz_local.responder(
        "¿Qué significa esto?",
        {"nivel_general": "rojo"},
        {"tono": "directo", "detalle": "completo", "recordatorios": "normal"},
    )
    assert resultado["fuente"] == "reglas_locales"
    assert "rojo" in resultado["texto"]
