#!/usr/bin/env python3
"""Puente entre una banda o pulsómetro Bluetooth Low Energy y el backend de ORBIT Health.

Lee la frecuencia cardíaca del servicio estándar (GATT 0x180D) y la envía cada pocos segundos a
/api/sensores/flujo/lote. Funciona sin internet. Requiere la librería opcional `bleak`:
    backend/.venv/bin/pip install -r backend/requirements-ble.txt

Uso:
    puente_ble.py --escanear                          # ¿qué dispositivos cercanos anuncian frecuencia cardíaca?
    puente_ble.py --nombre Polar --tripulante T1      # conecta y envía (sesión: variable ORBIT_TOKEN si hay autenticación)
    puente_ble.py --inspeccionar --nombre Aolon       # ¿qué servicios ofrece mi banda? ¿trae el estándar de frecuencia cardíaca?
    puente_ble.py --inspeccionar --nombre Aolon --escuchar 20   # además, muestra en crudo lo que emite durante 20 s

NO está probado con una banda real: confirma primero con --escanear que la tuya anuncia el servicio estándar.
"""
import argparse
import asyncio
import http.client
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("ORBIT_SEED_DEMO", "0")
from app.fuentes import ble  # noqa: E402


def _bleak():
    try:
        import bleak
        return bleak
    except ImportError:
        sys.exit("Falta la librería BLE. Instálala con: backend/.venv/bin/pip install -r backend/requirements-ble.txt")


async def escanear(segundos: float, mostrar: bool) -> int:
    bleak = _bleak()
    vistos = await bleak.BleakScanner.discover(timeout=segundos, return_adv=True)
    con_fc = [(d, a) for d, a in vistos.values() if ble.SERVICIO_FC in [u.lower() for u in (a.service_uuids or [])]]
    print(f"Dispositivos BLE visibles: {len(vistos)}")
    print(f"Los que anuncian el servicio estándar de frecuencia cardíaca: {len(con_fc)}")
    if mostrar:
        for d, a in con_fc:
            print(f"  - {d.name or '(sin nombre)'}  {d.address}  señal {a.rssi} dBm")
    elif con_fc:
        print("  (usa --mostrar para ver sus nombres y direcciones)")
    return 0 if con_fc else 1


def enviar(url: str, token: str | None, tripulante: str, muestras: list[dict]) -> bool:
    destino = urlparse(url)
    cabeceras = {"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})}
    try:
        c = http.client.HTTPConnection(destino.hostname, destino.port or 80, timeout=10)
        c.request("POST", "/api/sensores/flujo/lote", json.dumps({"tripulante_id": tripulante, "dispositivo_id": "puente-ble", "muestras": muestras}), cabeceras)
        r = c.getresponse(); r.read(); c.close()
        if r.status == 401:
            sys.exit("El servidor pide sesión: define la variable ORBIT_TOKEN con un token válido.")
        return r.status == 200
    except OSError:
        return False


async def _buscar(bleak, args):
    print("Buscando el dispositivo…")
    if args.direccion:
        dispositivo = await bleak.BleakScanner.find_device_by_address(args.direccion, timeout=10)
    else:
        dispositivo = await bleak.BleakScanner.find_device_by_filter(
            lambda d, a: bool(args.nombre) and args.nombre.lower() in (d.name or "").lower(), timeout=10)
    if dispositivo is None:
        print("No se encontró. Revisa que esté encendido y cerca, que NO esté conectado a la app del teléfono "
              "(muchas bandas solo aceptan una conexión) y usa --escanear.")
    return dispositivo


async def inspeccionar(args) -> int:
    """Conecta SOLO a tu dispositivo y muestra sus servicios; con --escuchar, también lo que emite en crudo."""
    bleak = _bleak()
    dispositivo = await _buscar(bleak, args)
    if dispositivo is None:
        return 1
    async with bleak.BleakClient(dispositivo) as cliente:
        resumen = ble.describir_gatt(cliente.services)
        print(f"\nServicios que ofrece ({resumen['servicios']}):")
        print("\n".join(resumen["lineas"]))
        if resumen["tiene_frecuencia_estandar"]:
            print("\nTRAE el servicio estándar de frecuencia cardíaca: el puente puede usarlo (puente_ble.py --nombre ...).")
        else:
            print("\nNO trae el servicio estándar de frecuencia cardíaca: habla un protocolo propio de su fabricante.")
        if args.escuchar > 0 and resumen["notificables"]:
            print(f"\nEscuchando {args.escuchar:g} s (esto muestra datos de TU dispositivo; no lo compartas si no quieres):")
            def mostrar(ch, datos):
                print(f"  {str(getattr(ch, 'uuid', ch))[:8]}…  {bytes(datos).hex()}")
            for uuid in resumen["notificables"]:
                try:
                    await cliente.start_notify(uuid, mostrar)
                except Exception as e:                      # algunas características exigen emparejar o autenticar
                    print(f"  {uuid[:8]}…  no se pudo escuchar ({type(e).__name__})")
            await asyncio.sleep(args.escuchar)
    return 0


async def transmitir(args) -> int:
    bleak = _bleak()
    token = os.environ.get("ORBIT_TOKEN")
    pendientes: list[dict] = []
    dispositivo = await _buscar(bleak, args)
    if dispositivo is None:
        return 1

    def al_recibir(_, datos: bytearray):
        try:
            fc = ble.muestra_valida(ble.parsear_medicion_fc(bytes(datos)))
        except ValueError:
            return
        if fc is not None:
            pendientes.append({"indicador": "frecuencia_cardiaca", "valor": fc})

    async with bleak.BleakClient(dispositivo) as cliente:
        await cliente.start_notify(ble.CARACTERISTICA_FC, al_recibir)
        print(f"Conectado. Enviando a {args.url} cada {args.cada} s. Ctrl+C para terminar.")
        try:
            while cliente.is_connected:
                await asyncio.sleep(args.cada)
                if pendientes:
                    lote = pendientes[:500]
                    if enviar(args.url, token, args.tripulante, lote):
                        del pendientes[:len(lote)]
                    else:
                        print(f"Sin respuesta del servidor; {len(pendientes)} muestras en espera (se reintenta).")
        except asyncio.CancelledError:
            pass
        finally:
            enviar_final = enviar(args.url, token, args.tripulante, pendientes[:500]) if pendientes else True
            print("Desconectado." + ("" if enviar_final else " Quedaron muestras sin enviar."))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--escanear", action="store_true", help="solo busca dispositivos con frecuencia cardíaca")
    p.add_argument("--mostrar", action="store_true", help="con --escanear, muestra nombres y direcciones")
    p.add_argument("--inspeccionar", action="store_true", help="conecta a tu dispositivo y lista sus servicios")
    p.add_argument("--escuchar", type=float, default=0, help="con --inspeccionar, segundos de datos en crudo")
    p.add_argument("--segundos", type=float, default=8, help="duración del escaneo")
    p.add_argument("--nombre", help="parte del nombre del dispositivo")
    p.add_argument("--direccion", help="dirección Bluetooth del dispositivo")
    p.add_argument("--tripulante", default="T1")
    p.add_argument("--url", default="http://127.0.0.1:3000")
    p.add_argument("--cada", type=float, default=5, help="segundos entre envíos")
    args = p.parse_args()
    if args.escanear:
        return asyncio.run(escanear(args.segundos, args.mostrar))
    if not (args.nombre or args.direccion):
        p.error("indica --nombre o --direccion (o usa --escanear)")
    try:
        return asyncio.run(inspeccionar(args) if args.inspeccionar else transmitir(args))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
