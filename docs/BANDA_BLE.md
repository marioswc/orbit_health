# Conectar una banda o un pulsómetro por Bluetooth

Objetivo: que la frecuencia cardíaca llegue sola, sin teclearla. Funciona sin internet.

## Qué hay y qué no

| Pieza | Estado |
|---|---|
| Intérprete del servicio estándar de frecuencia cardíaca de Bluetooth LE (`backend/app/fuentes/ble.py`) | Probado con paquetes de ejemplo del formato estándar (13 pruebas) |
| Entrada de un flujo continuo (`POST /api/sensores/flujo`, `/flujo/lote`, `/flujo/vaciar`) | Probada: 600 muestras en 10 minutos producen unas 11 lecturas, no 600; un valor extremo pasa al instante |
| Puente (`scripts/puente_ble.py`) | Probado contra el servidor real con una banda **simulada**. El escaneo funcionó con el Bluetooth real de esta laptop |
| Conexión con **una banda real** | **No probada**: no había ninguna a mano |
| SpO₂, temperatura y presión desde una banda comercial | **No cubierto.** Suelen usar protocolos propios de cada fabricante; hacerlo exigiría uno por marca |

## Cómo se usa

```bash
backend/.venv/bin/pip install -r backend/requirements-ble.txt           # una vez, con internet
backend/.venv/bin/python scripts/puente_ble.py --escanear --mostrar     # ¿mi dispositivo anuncia frecuencia cardíaca?
./run.sh                                                                # en otra terminal
backend/.venv/bin/python scripts/puente_ble.py --nombre "<parte del nombre>" --tripulante T1
```

Con la autenticación activada, define antes `ORBIT_TOKEN` con un token de sesión (no se pasa por argumento para que no
quede en el historial de la terminal).

## Cómo decide qué guardar
1. El puente lee cada notificación del dispositivo y **descarta** las que llegan sin contacto con la piel, con 0 o fuera de rango.
2. El servidor agrupa en ventanas de `ORBIT_FLUJO_VENTANA_S` (60 s por defecto) y guarda la **mediana**, que resiste un artefacto de movimiento.
3. Un valor **extremo** (el que por sí solo sería rojo) se guarda al instante, con un mínimo de `ORBIT_FLUJO_ENFRIAMIENTO_S` (30 s) entre extremos del mismo indicador para no inundar la cola de salida en una crisis.
4. Si el servidor no responde, el puente conserva las muestras y reintenta.

Un matiz: igual que con la captura manual, la **lectura más reciente es la que define el estado actual**. Un pico aislado queda registrado y enviado como rojo, pero si la lectura siguiente es normal, el estado vuelve a verde.

## Alternativas
- **Desde el navegador (Web Bluetooth)**, sin el puente: el frontend se conecta a la banda y envía a `/api/sensores/flujo/lote`. Funciona en Chrome o Edge desde `localhost`; en Linux puede requerir activar una opción del navegador. No se probó.
- **App móvil**: no está hecha. Desde un teléfono, Web Bluetooth exige HTTPS, así que no basta con abrir la dirección de la laptop por la red.

## Qué hay que comprobar con una banda real
- Que anuncie el servicio estándar (`--escanear`). Muchas bandas de muñeca no lo hacen, o solo si se activa un modo de transmisión de frecuencia cardíaca; un pulsómetro de pecho suele hacerlo.
- Que `puente_ble.py` conecte y mantenga la conexión durante varios minutos.
- Que el valor que muestra la interfaz coincida con el de la pantalla del dispositivo.
