# 04 — Sensores, Flujo Continuo, Bluetooth (BLE) y Origen de Datos

Además de la captura manual, **ORBIT Health** está preparado para recibir signos vitales directamente desde dispositivos portátiles (como bandas cardíacas o relojes). Este módulo explica cómo se resolvió la entrada de sensores sin saturar el sistema y cómo se mantiene la honestidad entre datos reales y simulados.

---

## 1. Entrada de Sensores Individual y por Lote ("Todo o Nada")

### Qué problema había
Un dispositivo puede enviar una sola lectura o un paquete de varias lecturas acumuladas (por ejemplo, tras reconectarse por Bluetooth). Si dentro de un paquete de 50 lecturas venía una corrupta o con un valor imposible, guardar solo la mitad dejaba el registro incompleto y confuso.

### Cómo se solucionó (`commit 7cf242e`)
En `backend/app/api/sensores.py`:
- **`POST /api/sensores/lectura`:** recibe una medición de un sensor y le aplica exactamente las mismas reglas clínicas (NEWS2, línea base, reglas combinadas y cola hacia Tierra) que a una medición manual.
- **`POST /api/sensores/lote`:** permite enviar hasta 100 lecturas de golpe bajo la regla de **"todo o nada"**: primero valida que todas las lecturas del paquete tengan indicadores y valores válidos; si una sola falla, rechaza el paquete entero sin ensuciar la base de datos.

---

## 2. El Problema del Flujo Continuo (1 muestra por segundo)

### Qué problema había
Una banda cardíaca Bluetooth envía aproximadamente **1 dato por segundo**. Si guardáramos cada segundo en la base de datos y en la cola hacia Tierra, en solo 10 minutos tendríamos **600 registros por tripulante** (miles por hora), inundando la pantalla, el disco y el enlace espacial con datos repetitivos. Pero tampoco podíamos simplemente esperar 1 minuto si al segundo 5 el tripulante sufría un paro o una caída grave de oxígeno.

### Cómo se solucionó (`commit 653fdc5`)
En `backend/app/dominio/flujo.py` y `backend/app/servicios/flujo.py` (`POST /api/sensores/flujo`, `POST /api/sensores/flujo/lote` y `POST /api/sensores/flujo/vaciar`) se diseñó un filtro inteligente en dos vías:

1. **Agrupación por ventanas de tiempo (`ORBIT_FLUJO_VENTANA_S`, 60 s por defecto):**
   - Mientras los valores sean normales o moderados, el sistema los acumula en memoria durante 60 segundos.
   - Al cumplirse el minuto, calcula la **mediana** (el valor central ordenado) y guarda **una sola lectura representativa**.
   - *¿Por qué la mediana y no el promedio?* Porque si el astronauta golpea la muñeca y el sensor marca por un segundo un pico falso de 210, la mediana ignora ese ruido, mientras que el promedio se alteraría. Así, 600 muestras en 10 minutos producen ~10 lecturas limpias en vez de 600.
2. **Paso inmediato para emergencias con enfriamiento (`ORBIT_FLUJO_ENFRIAMIENTO_S`, 30 s por defecto):**
   - Si llega una muestra con un **valor extremo** (el que por sí solo merece nivel **rojo**, como frecuencia cardíaca ≥ 131 o ≤ 40, o SpO₂ ≤ 91 %), **no espera a que termine el minuto: se guarda y se encola al instante**.
   - Para evitar que una crisis de 2 minutos envíe 120 alertas rojas seguidas cada segundo, tras registrar un extremo se activa un tiempo de **enfriamiento de 30 segundos** para ese mismo indicador antes de disparar otro extremo inmediato.

---

## 3. Intérprete Bluetooth (BLE) y Puente al Backend

### Qué problema había
Las bandas de frecuencia cardíaca comerciales hablan por Bluetooth Low Energy (BLE) enviando paquetes de bytes en el formato estándar GATT (`0x180D` / `0x2A37`), donde los datos vienen compactados en bits (indicando si el pulso viene en 1 o 2 bytes y si el sensor está tocando la piel).

### Cómo se solucionó (`commit 926a62b`)
- **Decodificador puro (`backend/app/fuentes/ble.py`):** traduce los bytes del estándar Bluetooth y extrae la frecuencia cardíaca, la energía gastada y los intervalos entre latidos (`RR-intervals`).
- **Filtro contra lecturas falsas:** si los bits de la banda indican que **se perdió el contacto con la piel**, o si el pulso viene en `0` o fuera del rango humano válido, el paquete se descarta automáticamente para no generar una falsa alarma roja cuando el tripulante se quita la banda.
- **Script puente (`scripts/puente_ble.py`):** se conecta por Bluetooth desde la computadora, lee los paquetes en vivo y los envía a `POST /api/sensores/flujo`. Si el servidor local no responde temporalmente, el puente guarda las muestras en una cola local y reintenta sin perderlas. *(Nota: probado con escaneo Bluetooth real de laptop y paquetes simulados; pendiente de probar con una banda física real, como se detalla en [BANDA_BLE.md](../../docs/BANDA_BLE.md)).*

---

## 4. Transparencia en el Origen de los Datos (`sensor` vs `simulado`)

### Qué problema había
Durante las pruebas (`commit 23d9b13`), se detectó que tanto la misión simulada en vivo como el botón de dispositivo simulado (`/api/demo/sensor/{tid}`) guardaban sus datos con `origen = 'sensor'`, y los escenarios de demostración los guardaban como `origen = 'manual'`. Esto provocaba que en la base de datos, en las gráficas, en los informes y en los mensajes a Tierra **fuera imposible distinguir un dato real de uno fabricado por el simulador**.

### Cómo se solucionó (`commit 23d9b13`)
- La base de datos distingue 4 orígenes claros:
  1. `manual`: escrito por un tripulante en el formulario.
  2. `sensor`: enviado por un dispositivo físico real.
  3. `simulado`: generado por cualquier simulador, escenario de demo o misión en vivo.
  4. `calibracion`: series históricas precargadas (PhysioNet BIDMC) para dar contexto de 14 días, que nunca se envían a Tierra.
- Las rutas de sensores (`/api/sensores/lectura`, `/api/sensores/lote`, `/api/sensores/flujo` y `/api/sensores/flujo/lote`) ahora aceptan explícitamente `"origen": "sensor"` (por defecto) o `"origen": "simulado"`, rechazando cualquier intento de inyectar datos como `manual` o `calibracion`.
- El campo `origen` viaja dentro del paquete hacia Tierra y aparece en el historial y en `/api/informe`, garantizando trazabilidad total.
