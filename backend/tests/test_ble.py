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
