import pytest

from app.fuentes import ble


def test_frecuencia_en_un_byte():
    assert ble.parsear_medicion_fc(bytes([0x00, 72])) == {"fc": 72, "contacto": None, "rr_ms": []}


def test_frecuencia_en_dos_bytes_little_endian():
    assert ble.parsear_medicion_fc(bytes([0x01, 0x2C, 0x01]))["fc"] == 300      # 0x012C


def test_intervalos_rr_en_unidades_de_un_1024avo_de_segundo():
    m = ble.parsear_medicion_fc(bytes([0x10, 60, 0x00, 0x04, 0x00, 0x02]))      # 1024 y 512 unidades
    assert m["fc"] == 60 and m["rr_ms"] == [1000.0, 500.0]


def test_energia_gastada_se_salta_y_los_rr_siguen_siendo_correctos():
    m = ble.parsear_medicion_fc(bytes([0x18, 80, 0x0A, 0x00, 0x00, 0x04]))
    assert m["fc"] == 80 and m["rr_ms"] == [1000.0]


@pytest.mark.parametrize("banderas,esperado", [(0x00, None), (0x04, False), (0x06, True), (0x02, None)])
def test_estado_de_contacto_con_la_piel(banderas, esperado):
    assert ble.parsear_medicion_fc(bytes([banderas, 70]))["contacto"] is esperado


@pytest.mark.parametrize("paquete", [b"", bytes([0x01, 0x2C]), bytes([0x08, 70, 0x01])])
def test_paquetes_vacios_o_truncados_se_rechazan(paquete):
    with pytest.raises(ValueError):
        ble.parsear_medicion_fc(paquete)


def test_sin_contacto_o_valor_imposible_no_se_envia_nada():
    assert ble.muestra_valida({"fc": 72, "contacto": True, "rr_ms": []}) == 72.0
    assert ble.muestra_valida({"fc": 72, "contacto": None, "rr_ms": []}) == 72.0
    assert ble.muestra_valida({"fc": 72, "contacto": False, "rr_ms": []}) is None      # banda sin tocar la piel
    assert ble.muestra_valida({"fc": 0, "contacto": True, "rr_ms": []}) is None         # lectura vacía habitual al conectar
    assert ble.muestra_valida({"fc": 300, "contacto": True, "rr_ms": []}) is None       # fuera del rango del catálogo


def test_los_identificadores_son_los_estandar_de_bluetooth():
    assert ble.SERVICIO_FC.startswith("0000180d") and ble.CARACTERISTICA_FC.startswith("00002a37")


def test_el_puente_arranca_y_muestra_su_ayuda_sin_necesitar_bluetooth():
    import subprocess
    import sys
    from pathlib import Path
    script = Path(__file__).resolve().parents[2] / "scripts" / "puente_ble.py"
    r = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0 and "--escanear" in r.stdout and "NO está probado con una banda real" in r.stdout


# ---------- inspección de la tabla GATT (con servicios simulados, sin conectar a ningún dispositivo) ----------
from types import SimpleNamespace as NS


def _servicio(uuid, *caracteristicas):
    return NS(uuid=uuid, characteristics=[NS(uuid=u, properties=p) for u, p in caracteristicas])


def test_un_dispositivo_con_el_servicio_estandar_se_reconoce_y_marca_sus_notificaciones():
    r = ble.describir_gatt([
        _servicio(ble.SERVICIO_FC.upper(), (ble.CARACTERISTICA_FC, ["notify"]), ("00002a38-0000-1000-8000-00805f9b34fb", ["read"])),
        _servicio("0000180f-0000-1000-8000-00805f9b34fb", ("00002a19-0000-1000-8000-00805f9b34fb", ["read", "notify"]))])
    assert r["tiene_frecuencia_estandar"] is True and r["servicios"] == 2
    assert ble.CARACTERISTICA_FC in r["notificables"] and any("ESTÁNDAR" in l for l in r["lineas"])


def test_una_banda_de_consumo_con_protocolo_propio_se_reconoce_como_tal():
    r = ble.describir_gatt([_servicio("0000fee7-0000-1000-8000-00805f9b34fb", ("0000fec8-0000-1000-8000-00805f9b34fb", ["indicate"])),
                            _servicio("6e400001-b5a3-f393-e0a9-e50e24dcca9e", ("6e400003-b5a3-f393-e0a9-e50e24dcca9e", ["notify"]))])
    assert r["tiene_frecuencia_estandar"] is False and r["servicios"] == 2
    assert len(r["notificables"]) == 2 and not any("ESTÁNDAR" in l for l in r["lineas"])


def test_las_propiedades_salen_en_orden_estable_y_sin_servicios_no_hay_nada():
    r = ble.describir_gatt([_servicio("0000aaaa-0000-1000-8000-00805f9b34fb", ("0000bbbb-0000-1000-8000-00805f9b34fb", ["write", "read", "notify"]))])
    assert "[notify,read,write]" in r["lineas"][1]
    assert ble.describir_gatt([]) == {"lineas": [], "tiene_frecuencia_estandar": False, "notificables": [], "servicios": 0}


def test_la_ayuda_del_puente_explica_como_inspeccionar_una_banda():
    import subprocess, sys
    from pathlib import Path
    script = Path(__file__).resolve().parents[2] / "scripts" / "puente_ble.py"
    r = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0 and "--inspeccionar" in r.stdout and "--escuchar" in r.stdout


# ---------- elegir entre varios dispositivos con el mismo nombre, sin adivinar ----------
def _c(nombre, rssi, direccion):
    return (nombre, rssi, direccion, object())


def test_sin_coincidencias_no_hay_dispositivo():
    assert ble.elegir_coincidencia([]) == ("ninguna", None)


def test_una_sola_coincidencia_se_usa():
    estado, item = ble.elegir_coincidencia([_c("Aolon Curve", -60, "AA:05:27")])
    assert estado == "unica" and item[2] == "AA:05:27"


def test_con_varias_iguales_no_elige_solo_y_las_ordena_por_senal():
    estado, lista = ble.elegir_coincidencia([_c("Aolon Curve", -72, "B"), _c("Aolon Curve", -58, "A"), _c("Aolon Curve", -90, "C")])
    assert estado == "ambigua" and [x[2] for x in lista] == ["A", "B", "C"]


def test_con_mas_cercana_elige_la_de_senal_mas_fuerte():
    estado, item = ble.elegir_coincidencia([_c("Aolon Curve", -72, "B"), _c("Aolon Curve", -58, "A")], mas_cercana=True)
    assert estado == "unica" and item[2] == "A"


def test_una_senal_desconocida_no_gana_a_una_conocida():
    estado, item = ble.elegir_coincidencia([_c("X", None, "N"), _c("X", -80, "K")], mas_cercana=True)
    assert item[2] == "K"


# ---------- aprovechamiento de intervalos RR para variabilidad cardíaca (RMSSD) ----------
def test_calcular_rmssd_desde_intervalos_rr_y_filtrado_de_artefactos():
    # Diferencias sucesivas: +40, -30, +40 -> media cuadrática = (1600 + 900 + 1600)/3 = 1366.67 -> sqrt = 37.0 ms
    assert ble.calcular_rmssd([800.0, 840.0, 810.0, 850.0]) == 37.0
    # Un salto ectópico/artefacto (>35%) entre 820 y 1600 se descarta sin contaminar el RMSSD
    assert ble.calcular_rmssd([800.0, 820.0, 1600.0, 810.0]) == 20.0
    # Menos de 2 intervalos válidos o fuera del rango humano devuelve None
    assert ble.calcular_rmssd([800.0]) is None
    assert ble.calcular_rmssd([100.0, 3500.0]) is None


def test_extraer_muestras_acumula_rr_entre_paquetes_y_limpia_al_perder_contacto():
    ventana: list[float] = []
    # Primer paquete con 2 intervalos RR: con min_rr=4 aún solo emite frecuencia_cardiaca
    m1 = ble.parsear_medicion_fc(bytes([0x16, 72, 0x40, 0x03, 0x60, 0x03]))
    s1 = ble.extraer_muestras(m1, ventana, min_rr=4)
    assert s1 == [{"indicador": "frecuencia_cardiaca", "valor": 72.0}]
    assert len(ventana) == 2

    # Segundo paquete con otros 2 intervalos RR: ya suma 4 y emite frecuencia_cardiaca + variabilidad_cardiaca
    m2 = ble.parsear_medicion_fc(bytes([0x16, 71, 0x38, 0x03, 0x58, 0x03]))
    s2 = ble.extraer_muestras(m2, ventana, min_rr=4)
    assert [x["indicador"] for x in s2] == ["frecuencia_cardiaca", "variabilidad_cardiaca"]
    assert 10.0 <= s2[1]["valor"] <= 60.0

    # Si se pierde el contacto con la piel (bandera 0x04), no emite muestras y limpia la ventana RR
    sin_contacto = ble.parsear_medicion_fc(bytes([0x04, 72]))
    assert ble.extraer_muestras(sin_contacto, ventana, min_rr=4) == []
    assert ventana == []


def test_variabilidad_cardiaca_solo_avisa_cuando_cae_bajo_la_linea_base(cliente):
    for v in (48, 50, 46, 49, 47, 50):
        cliente.post("/api/sensores/lectura", json={"tripulante_id": "T1", "indicador": "variabilidad_cardiaca", "valor": v})
    # Subir la variabilidad cardíaca (mejor tono vagal) nunca es alerta
    alta = cliente.post("/api/sensores/lectura", json={"tripulante_id": "T1", "indicador": "variabilidad_cardiaca", "valor": 75}).json()
    assert alta["aviso_linea_base"] is False and alta["nivel"] == "verde"
    # Una caída pronunciada por debajo de la base sí activa el aviso amarillo de seguimiento
    baja = cliente.post("/api/sensores/lectura", json={"tripulante_id": "T1", "indicador": "variabilidad_cardiaca", "valor": 24}).json()
    assert baja["aviso_linea_base"] is True and baja["nivel"] == "amarillo"
