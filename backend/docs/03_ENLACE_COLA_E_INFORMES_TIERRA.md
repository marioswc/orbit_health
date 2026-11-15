# 03 — Enlace con Tierra, Cola con Prioridad e Informes

En misiones a la Luna o a Marte, las comunicaciones se cortan por eclipses o conjunciones solares y los mensajes tardan desde segundos hasta 20 minutos en viajar en un solo sentido. Este módulo garantiza que **ningún evento médico se pierda cuando cae el enlace** y que, al reconectar, **las emergencias salgan primero**.

---

## 1. Cola de Salida (Modo Eclipse) y Estado Persistente

### Qué problemas había
1. Al inicio (`commit f84fcc0`), el estado de si había conexión con Tierra o Modo Eclipse se guardaba en la memoria temporal del servidor: si el programa se reiniciaba, olvidaba que estaba en eclipse.
2. Cuando ocurría un corte de señal, los eventos médicos necesitaban guardarse en orden y despacharse automáticamente en cuanto volviera el enlace.

### Cómo se solucionó (`commits ed8a8bc`, `f84fcc0`, `6040556`)
- **Estado persistente en base de datos (`backend/app/repositorios/enlace.py`):** la tabla `estado_enlace` guarda si el enlace está `activo` o en eclipse (`activo = 0`) y en qué entorno está la misión (`luna`, `marte_cercano`, `marte_medio`, `marte`).
- **Cola con prioridad (`backend/app/servicios/cola.py`):**
  - Cada vez que se registra una lectura clínica (`POST /api/lecturas` o vía sensores), se crea un evento en `cola_salida` con prioridad según su gravedad:
    - **Prioridad 1:** Rojo (emergencia)
    - **Prioridad 2:** Amarillo (aviso preventivo)
    - **Prioridad 3:** Verde (rutina)
  - Si el enlace está en **Modo Eclipse**, todos los eventos quedan con estado `retenido` a bordo.
  - En cuanto el enlace vuelve a estar activo (`POST /api/enlace`), el sistema drena la cola sacando **primero todos los de Prioridad 1, luego Prioridad 2 y al final Prioridad 3**, respetando el orden de antigüedad dentro de cada prioridad.
- **Resumen automático de rutina tras un apagón largo (`compactar_rutina`, `commit 20312e7`):**
  - *Qué problema había:* durante un corte de señal largo (como una conjunción solar), las bandas acumulan más de cien lecturas verdes (prioridad 3, sin novedad). Al volver el enlace, enviar cientos de mensajes rutinarios uno por uno ocupaba el canal con datos sin novedad, pero tampoco se podían borrar de la tabla `cola_salida` porque se rompería la cadena de hash de integridad (`SHA-256`).
  - *Cómo se solucionó:* cuando se acumulan al menos `ORBIT_COMPACTAR_RUTINA_DESDE` (20 por defecto) eventos de rutina (prioridad 3) retenidos, al reconectar el enlace el sistema marca esos registros individuales con `resumido = 1` (**no los borra**, por lo que siguen guardados a bordo y la cadena de hash en `GET /api/cola/verificar` se mantiene intacta) y genera **un único evento `resumen_rutina` por tripulante** con la cantidad de lecturas agrupadas y el rango de horas. Los eventos amarillos (prioridad 2) y rojos (prioridad 1) **nunca se resumen** y salen íntegros al frente de la fila.

---

## 2. Simulación Realista de Distancia (Luna y Marte)

### Qué problema había
Salir de la nave no significa llegar al instante a Tierra: una señal desde Marte puede tardar entre 4 y 20 minutos en llegar (`en_transito`), y la confirmación de recibido tarda otro tanto en volver. Además, esperar 20 minutos reales durante una demostración frente al jurado no era práctico.

### Cómo se solucionó (`commits 4be3198`, `334b7e0`)
En `backend/app/datos/enlace.json` y `backend/app/dominio/enlace.py`:
- Se definieron perfiles de retardo para `luna` (~1.3 s), `marte_cercano` (4 min), `marte_medio` (12 min) y `marte` (20 min).
- **Cálculo de llegada y confirmación:** cuando un evento sale de la nave, el sistema calcula a qué hora exacta llegará a Tierra (`llegada_estimada_ts`) y a qué hora llegará de regreso la confirmación a la nave (`ack_estimado_ts`), agregando una pequeña variación opcional (*jitter*) con semilla reproducible para simular fluctuaciones del canal.
- **Factor de aceleración (`ORBIT_FACTOR_ACELERACION`):** permite acelerar el reloj de viaje de las señales (por ejemplo, 60 veces más rápido) para ver en segundos cómo un mensaje pasa de `retenido` a `en_transito`, luego a `recibido` en Tierra y finalmente a `confirmado` a bordo (`GET /api/enlace/latencia` y `GET /api/cola`).

---

## 3. Vista del Centro de Control en Tierra (`/api/tierra/mensajes`)

### Qué problema había
Se necesitaba una pantalla donde el equipo médico en Tierra viera lo que va llegando desde la nave, pero con dos requisitos críticos:
1. Tierra **no puede ver** mensajes que siguen viajando por el espacio (`en_transito`) ni los que siguen atrapados en la nave por un eclipse (`retenido`).
2. Consultar la bandeja desde Tierra **no debe consumir ni borrar** los mensajes: si dos médicos en Tierra abren la pantalla o recargan el navegador, ambos deben ver exactamente lo mismo sin que se pierda nada.

### Cómo se solucionó (`commit ad2ad54`)
- La ruta `GET /api/tierra/mensajes` es **100 % de solo lectura e idempotente** (leerla diez veces devuelve el mismo resultado sin alterar la cola).
- Filtra únicamente los mensajes cuya hora estimada de llegada (`llegada_estimada_ts`) ya se cumplió respecto al reloj actual, ordenándolos con **lo más urgente primero**, e informa cuántos mensajes siguen viajando en camino y cuántos siguen retenidos a bordo.
- Se añadió un índice especial en la base de datos (`idx_cola_llegada`) para que esta consulta sea instantánea incluso cuando se acumulan cientos de eventos tras un apagón largo.

---

## 4. Cadena de Hash (Sello de Integridad) y Informes Exportables

### Qué problema había
En auditoría médica y aeroespacial es fundamental demostrar dos cosas:
1. Que ningún registro enviado a Tierra fue modificado, borrado o insertado a escondidas.
2. Con qué versión exacta de las reglas médicas se tomó cada decisión en su momento.

### Cómo se solucionó (`commits ed8a8bc`, `0f0728a`, `d38c439`)
- **Hash encadenado (`backend/app/dominio/integridad.py`):** cada evento que entra a la cola calcula una huella digital (`SHA-256`) que incluye los datos del evento, la fecha exacta y **la huella del evento anterior** (`hash_prev`), formando una cadena como los eslabones de un candado. Si alguien altera un solo número en la base de datos, la ruta `GET /api/cola/verificar` detecta inmediatamente en qué fila se rompió la cadena.
- **Versión de reglas en cada evento:** cada mensaje guarda la versión y el estado de validación de `umbrales.json` vigentes cuando se evaluó la lectura.
- **Informes listos para Tierra (`GET /api/informe` y `GET /api/informe/{tid}`):**
  - Generan un reporte completo de toda la tripulación o de un tripulante en formato **JSON** o **CSV** (listo para abrir en una hoja de cálculo en Tierra).
  - Incluyen su propia huella de integridad `SHA-256` verificable y **excluyen por diseño el diario privado, los tamizajes PHQ-2 y el ánimo diario**.
