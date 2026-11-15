# Documentación del Backend por Capas, Módulos e Integraciones

Esta guía explica de forma clara, directa y sin exceso de tecnicismos **todos los cambios, módulos y soluciones** que se construyeron en el backend de **ORBIT Health**, tomando como base el historial real de commits del repositorio.

En lugar de concentrar todo en un solo archivo gigante, la documentación está dividida por cada capa, módulo e integración para que puedas consultar exactamente **qué problema existía, cómo se resolvió y en qué archivos vive cada solución**.

---

## Índice de documentos

1. **[01 — Motor Clínico, Reglas Combinadas y Línea Base Personal](01_MOTOR_CLINICO_Y_LINEA_BASE.md)**
   Cómo el sistema evalúa signos vitales (NEWS2, glucosa, sueño, ejercicio, aire de cabina), cómo cruza señales para detectar problemas grupales de CO₂ y cómo se corrigieron las falsas alarmas de la línea base personal.
2. **[02 — Bienestar, Salud Mental, Crisis y Hábitos](02_BIENESTAR_SALUD_MENTAL_Y_HABITOS.md)**
   Cómo se protege la privacidad del diario y del ánimo, cómo funciona el protocolo de crisis psicológica cruzado con el oxígeno de cabina, los avisos con consentimiento al médico, el asistente adaptable y la racha de mediciones.
3. **[03 — Enlace con Tierra, Cola con Prioridad e Informes](03_ENLACE_COLA_E_INFORMES_TIERRA.md)**
   Cómo funciona el Modo Eclipse, el envío ordenado por urgencia al recuperar señal, la simulación de distancia (Luna y Marte), la vista del centro de control en Tierra y los informes exportables con sello de integridad.
4. **[04 — Sensores, Flujo Continuo, Bluetooth (BLE) y Origen de Datos](04_SENSORES_FLUJO_Y_BLUETOOTH.md)**
   Cómo se reciben datos continuos sin saturar la base de datos (ventanas de 1 minuto con paso inmediato para emergencias), el puente para bandas Bluetooth y cómo se distingue un sensor real de una simulación.
5. **[05 — Conocimiento Espacial: Riesgos NASA, Explicaciones y Entornos](05_CONOCIMIENTO_ESPACIAL_NASA.md)**
   Cómo se integraron los peligros oficiales de la NASA, las citas textuales con enlaces reales y el cálculo de gravedad y pérdida ósea según el entorno (nave, estación, Luna o Marte).
6. **[06 — Seguridad a Bordo, Simulación en Vivo y Pruebas de Calidad](06_SEGURIDAD_SIMULACION_Y_CALIDAD.md)**
   Cómo funciona el acceso con PIN sin internet, los permisos ante emergencias, la misión simulada en vivo que corre sola para demostraciones y las pruebas automáticas que vigilan la seguridad y la documentación.
7. **[07 — IA Local Explicativa y Asistente de Voz Offline](07_IA_LOCAL_Y_VOZ.md)**
   Cómo funciona el explicador opcional con IA local (`GET /api/estado/{tid}/explicacion`) y el chat de voz offline (`POST /api/voz/chat/{tid}`), garantizando que la IA solo explique resultados ya calculados sin alterar jamás el nivel clínico ni saturar la computadora a bordo.

> Para ver el plan inicial del proyecto puedes consultar [PLAN_DE_DESARROLLO.md](PLAN_DE_DESARROLLO.md), y para el listado completo de rutas disponibles consulta [API_REFERENCIA.md](../../docs/API_REFERENCIA.md).

---

## 1. Reorganización del Backend en 5 Capas

### Qué problema había
Al inicio del proyecto (`commits f0c3ec8` a `f0a7fe8`), toda la lógica estaba concentrada en muy pocos archivos sueltos dentro de `backend/app/`. Las rutas web, las consultas a la base de datos y las reglas médicas convivían en el mismo lugar. Además, cuando se guardaba una lectura médica y luego se metía a la cola de envío hacia Tierra, se hacía en dos pasos separados: si ocurría un error a la mitad, la lectura podía guardarse sin encolarse (o viceversa).

### Cómo se solucionó (`commits 0f0728a`, `e9a6ef8`)
Se dividió todo el backend en **5 carpetas (capas)** con responsabilidades muy claras:

| Capa / Carpeta | Qué hace en palabras simples |
|---|---|
| `backend/app/api/` | **La puerta de entrada.** Recibe las peticiones del navegador o de los sensores, revisa permisos y devuelve la respuesta. No hace cálculos médicos ni escribe SQL. |
| `backend/app/servicios/` | **El coordinador.** Conecta las piezas para cumplir cada tarea (por ejemplo: "registrar una lectura, evaluarla y meterla a la cola de Tierra en un solo paso"). |
| `backend/app/dominio/` | **El cerebro de reglas.** Contiene las fórmulas clínicas, umbrales, protocolos de crisis y sellos de seguridad. No depende de internet ni de la base de datos, por lo que es muy fácil de probar. |
| `backend/app/repositorios/` | **El archivero.** Es el único lugar donde se habla con la base de datos SQLite (`schema.sql`, consultas y respaldos). |
| `backend/app/fuentes/` | **Los alimentadores de datos.** Incluye los datos iniciales de prueba (`semilla.py`), el cargador de datos médicos reales para calibrar (`calibracion.py`), el traductor de Bluetooth (`ble.py`) y los guiones de simulación. |

Además, se unificó el registro de lecturas y su encolado a Tierra en **una sola operación atómica**: o se guardan ambos correctamente, o no se guarda ninguno.

---

## 2. Base de Datos Robusta y Sistema que se "Cura Solo"

### Qué problemas había
1. **Rutas relativas frágiles (`commits 4d8fa2c`, `9af21a0`):** dependiendo de desde qué carpeta se arrancara el servidor en la terminal, el archivo `orbit_health.db` se creaba en lugares distintos (incluso fuera del repositorio).
2. **Bloqueos y cortes de energía (`commit 4d8fa2c`):** si dos peticiones intentaban escribir al mismo tiempo (por ejemplo, una banda enviando datos mientras el tripulante abría su estado), SQLite podía bloquearse.
3. **Corrupción sin soporte técnico a bordo (`commits 6ca4551`, `b9d74b0`):** en una misión espacial no hay un administrador de sistemas para reparar la base de datos si un apagón daña el archivo.

### Cómo se solucionó
- **Ruta fija y segura (`backend/app/config.py`):** la base apunta siempre por defecto a `data/orbit_health.db` dentro del proyecto, sin importar desde dónde se ejecute el comando.
- **Modo resistente a fallos (`backend/app/repositorios/conexion.py`):** se activó el modo de escritura segura (`WAL`), espera automática ante accesos simultáneos (`busy_timeout`) y validación estricta de relaciones entre tablas (`foreign_keys=ON`).
- **Autocuración al arrancar (`backend/app/servicios/recuperacion.py`):**
  1. Cada vez que el servidor inicia, revisa la salud interna de la base de datos (`PRAGMA integrity_check`).
  2. Si detecta que el archivo está dañado, **no lo borra** (lo mueve a un archivo `.danada-<fecha>` como evidencia junto con sus archivos temporales).
  3. Busca automáticamente entre los respaldos guardados el más reciente que esté sano y **se restaura solo**.
  4. Si ningún respaldo sirve, arranca con una base limpia para que el sistema **nunca quede fuera de servicio** en plena misión.
- **Respaldos automáticos (`backend/app/repositorios/respaldo.py`):** al arrancar y cada cierto tiempo (`ORBIT_RESPALDO_CADA_MIN`, por defecto 30 minutos), el sistema saca una copia consistente de la base y borra las más antiguas para no llenar el disco (`ORBIT_RESPALDOS_CONSERVAR`).
- **Consulta sencilla del estado (`GET /api/salud`):** devuelve en lenguaje claro si la base está sana, cuántos respaldos existen y si hubo que restaurar algo al arrancar.
