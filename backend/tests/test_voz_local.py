from app import config
from app.servicios import voz_local


def test_normaliza_idioma_desde_locale():
    assert voz_local.normalizar_idioma("ES") == "es"
    assert voz_local.normalizar_idioma("en-US") == "en"
    assert voz_local.normalizar_idioma("auto") is None


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


def test_respuesta_de_voz_en_ingles_sin_modelo(monkeypatch):
    monkeypatch.setattr(config, "IA_LOCAL_URL", "")
    monkeypatch.setattr(config, "IA_LOCAL_MODELO", "")
    resultado = voz_local.responder(
        "How am I?",
        {"nivel_general": "verde"},
        {"tono": "directo"},
        idioma="en",
    )
    assert resultado["idioma"] == "en"
    assert "overall status is green" in resultado["texto"]


def test_voz_no_envia_datos_privados_al_modelo(monkeypatch):
    vistos = []
    monkeypatch.setattr(voz_local.explicador_local, "consultar_modelo", lambda p, **kw: vistos.append(p) or None)
    voz_local.responder(
        "¿Qué significa mi estado?",
        {
            "nivel_general": "amarillo",
            "nivel_fisiologico": "amarillo",
            "indicadores": [
                {"indicador": "spo2", "valor": 96, "nivel": "verde"},
                {"indicador": "animo", "valor": 1, "nivel": "amarillo"},
                {"indicador": "sueno_horas", "valor": 4, "nivel": "amarillo"},
            ],
            "news2": {"puntos": 2, "faltantes": []},
        },
        {"tono": "directo"},
    )
    assert '"indicador": "spo2"' in vistos[0]
    assert '"indicador": "animo"' not in vistos[0]
    assert '"indicador": "sueno_horas"' not in vistos[0]


def test_audio_invalido_se_expone_como_error_de_validacion(tmp_path):
    ruta = tmp_path / "audio.wav"
    ruta.write_bytes(b"no es audio")

    try:
        voz_local._decodificar_audio(str(ruta))
    except ValueError as error:
        assert str(error) == "Audio inválido o formato no compatible"
    else:
        raise AssertionError("El audio inválido debe producir ValueError")
