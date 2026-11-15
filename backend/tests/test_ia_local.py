import io
import json

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


def test_acepta_host_docker_internal_como_loopback_del_anfitrion():
    assert explicador_local._url_local("http://host.docker.internal:11434/api/generate") is True
    assert explicador_local._url_local("http://127.0.0.1:11434/api/generate") is True
    assert explicador_local._url_local("https://example.com/api/generate") is False


def test_endpoint_explica_estado_sin_recalcularlo(cliente):
    cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 88})
    respuesta = cliente.get("/api/estado/T1/explicacion")
    assert respuesta.status_code == 200
    assert respuesta.json()["nivel_general"] == "rojo"


def test_deepseek_se_usa_cuando_hay_api_key(monkeypatch):
    capturada = {}

    class _Respuesta:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "Tu nivel actual es verde."}}]}).encode("utf-8")

    def _abrir(req, timeout=0):
        capturada["url"] = req.full_url
        capturada["auth"] = req.get_header("Authorization")
        capturada["body"] = json.loads(req.data.decode("utf-8"))
        return _Respuesta()

    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "sk-prueba")
    monkeypatch.setattr(config, "DEEPSEEK_MODELO", "deepseek-flash")
    monkeypatch.setattr(config, "IA_PROVEEDOR", "")
    monkeypatch.setattr(explicador_local._ABRIDOR, "open", _abrir)

    resultado = explicador_local.explicar({"nivel_general": "verde", "news2": {"puntos": 0, "faltantes": []}})
    assert resultado["fuente"] == "deepseek"
    assert resultado["generado_por_ia"] is True
    assert resultado["explicacion"] == "Tu nivel actual es verde."
    assert capturada["auth"] == "Bearer sk-prueba"
    assert capturada["body"]["model"] == "deepseek-flash"


def test_proveedor_local_ignora_deepseek_api_key(monkeypatch):
    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "sk-prueba")
    monkeypatch.setattr(config, "IA_PROVEEDOR", "local")
    monkeypatch.setattr(config, "IA_LOCAL_URL", "")
    resultado = explicador_local.explicar({"nivel_general": "verde"})
    assert resultado["fuente"] == "reglas_locales"
