import csv
import hashlib
import io
import json
import sqlite3

from app import config


def lectura(c, ind, val, tid="T1", **kw):
    return c.post("/api/lecturas", json={"tripulante_id": tid, "indicador": ind, "valor": val}, **kw)


def _verifica_hash(informe: dict) -> bool:
    cuerpo = {k: v for k, v in informe.items() if k != "integridad_sha256"}
    canon = json.dumps(cuerpo, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest() == informe["integridad_sha256"]


def test_informe_de_tripulante_incluye_estado_lecturas_y_version_de_reglas(cliente):
    lectura(cliente, "spo2", 88)
    lectura(cliente, "temperatura", 36.8)
    r = cliente.get("/api/informe/T1").json()
    assert r["tripulante"]["id"] == "T1" and r["estado"]["nivel_general"] == "rojo"
    assert {x["indicador"] for x in r["lecturas_recientes"]} == {"spo2", "temperatura"}
    assert r["umbrales"]["version"] and r["umbrales"]["estado"].startswith("pendiente")
    assert r["estado"]["peligros_relacionados"] and "cola_de_salida" in r


def test_el_hash_de_integridad_se_puede_recomputar_y_detecta_cambios(cliente):
    lectura(cliente, "spo2", 97)
    r = cliente.get("/api/informe/T1").json()
    assert _verifica_hash(r) is True
    assert r["estado"]["nivel_general"] == "verde"
    r["estado"]["nivel_general"] = "rojo"          # alterar el contenido
    assert _verifica_hash(r) is False


def test_el_informe_nunca_incluye_datos_privados(cliente):
    cliente.post("/api/diario", json={"tripulante_id": "T1", "contenido": "texto muy privado XYZ"})
    cliente.post("/api/animo", json={"tripulante_id": "T1", "valor": 1})
    cliente.post("/api/tamizajes", json={"tripulante_id": "T1", "item1": 3, "item2": 3})
    lectura(cliente, "spo2", 97)
    for url in ("/api/informe/T1", "/api/informe"):
        texto = cliente.get(url).text
        assert "XYZ" not in texto and "animo" not in texto.lower().replace("ánimo diario", "")
        assert "tamizaje" not in texto.lower().replace("tamizajes ni", "")
    assert "privados" in cliente.get("/api/informe/T1").json()["aviso"]


def test_informe_de_la_tripulacion_resume_a_todos_y_la_alerta_colectiva(cliente):
    lectura(cliente, "co2", 3.6, tid="T3")
    lectura(cliente, "spo2", 90, tid="T1")
    lectura(cliente, "spo2", 92, tid="T2")
    lectura(cliente, "frecuencia_respiratoria", 26, tid="T2")
    r = cliente.get("/api/informe").json()
    assert {t["id"] for t in r["tripulacion"]} == {"T1", "T2", "T3", "T4"}
    assert r["alertas_colectivas"] and r["alertas_colectivas"][0]["afectados"] == 2
    assert r["enlace"]["entorno"] and _verifica_hash(r)


def test_csv_de_lecturas_en_orden_cronologico_y_con_cabecera(cliente):
    for v in (97, 98, 96):
        lectura(cliente, "spo2", v)
    r = cliente.get("/api/informe/T1?formato=csv")
    assert r.headers["content-type"].startswith("text/csv") and "orbit_T1.csv" in r.headers["content-disposition"]
    filas = list(csv.reader(io.StringIO(r.text)))
    assert filas[0] == ["ts", "indicador", "valor", "unidad", "nivel", "origen"]
    assert [f[2] for f in filas[1:]] == ["97.0", "98.0", "96.0"]


def test_el_informe_valida_el_tripulante(cliente):
    assert cliente.get("/api/informe/X").status_code == 404


def test_con_autenticacion_el_informe_exige_sesion(cliente_auth):
    assert cliente_auth.get("/api/informe").status_code == 401
    assert cliente_auth.get("/api/informe/T1").status_code == 401
    assert cliente_auth.get("/api/informe/T1", headers=cliente_auth.entrar("T3")).status_code == 200


def test_cada_evento_de_la_cola_guarda_la_version_de_las_reglas(cliente):
    lectura(cliente, "spo2", 88)
    conn = sqlite3.connect(config.DB_PATH)
    payload = json.loads(conn.execute("SELECT payload FROM cola_salida ORDER BY id DESC LIMIT 1").fetchone()[0])
    conn.close()
    assert payload["reglas_version"] and payload["reglas_estado"].startswith("pendiente")
