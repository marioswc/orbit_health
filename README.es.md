# ORBIT Health

Apoyo a la decisión clínica para tripulaciones con comunicación degradada. Funciona 100 % local.
**English:** [README.md](README.md). English summary for judges: [docs/PROJECT_SUMMARY_EN.md](docs/PROJECT_SUMMARY_EN.md). Use of SI tools (required by the challenge): [docs/SI_DISCLOSURE.md](docs/SI_DISCLOSURE.md).

Estado y pendientes del equipo: [docs/PENDIENTES.md](docs/PENDIENTES.md).

Plan completo: [PLAN_DE_DESARROLLO.md](docs/PLAN_DE_DESARROLLO.md).

## Producción local (un solo servidor, sin internet)

En una máquina nueva (necesita internet una sola vez; requiere Python 3.10+ y Node.js con npm):

```bash
scripts/asistente_inicio.sh   # asistente paso a paso que te hace preguntas (recomendado si es tu primera vez)
scripts/preparar.sh      # o, sin preguntas: entorno de Python, dependencias, compilación de la interfaz y .env
./run.sh                 # API y frontend en http://127.0.0.1:3000, sin internet
```

## Arranque y verificación rápidos

```bash
./run.sh                      # preparado una vez con red; luego funciona sin internet (solo 127.0.0.1)
scripts/verificar_e2e.sh      # E2E automático contra una base temporal
```

## Datos de calibración (opcional)

```bash
scripts/descargar_physionet.sh    # con red, una vez (ya versionado en data/physionet)
scripts/cargar_calibracion.sh     # sin red: carga series BIDMC como historial de los tripulantes demo
```

Los registros son de pacientes críticos hospitalizados (ver `data/physionet/ATRIBUCION.md`): sirven para dar
variabilidad realista a la demo, no como línea base clínica.

## Despliegue a bordo (más allá de `localhost`)

`localhost` es el modo de una sola estación. Para atender a toda la tripulación:

| Necesidad | Qué hay hoy | Qué falta |
|---|---|---|
| Arranque automático y reinicio si falla | `deploy/orbit-health.service` (systemd) | Probarlo en el equipo de destino |
| Atender otros dispositivos de la cabina | `ORBIT_HOST=0.0.0.0` exige `ORBIT_AUTH=1` (autenticación por tripulante con PIN, roles y auditoría; ver [docs/SEGURIDAD_A_BORDO.md](docs/SEGURIDAD_A_BORDO.md)) | TLS y cifrado de la base |
| Respaldo de datos | `scripts/respaldar_db.sh` (consistente, con rotación) | Programarlo (cron o systemd timer) y definir dónde se guarda |
| Sin Node ni internet en el destino | El build del frontend es estático y lo sirve el backend | Paquete de instalación con las dependencias de Python precargadas |

## Simular la latencia del enlace

| Modo | Configuración | Retardo de ida (Marte, peor caso) |
|---|---|---|
| Demo acelerada (por defecto) | `ORBIT_FACTOR_ACELERACION=30` | 40 s |
| Tiempo real | `ORBIT_FACTOR_ACELERACION=1` | 1200 s (20 min) |
| Con variación | `ORBIT_JITTER_PCT=15` y, para repetirlo, `ORBIT_JITTER_SEMILLA=42` | ±15 % |

- Perfiles en `backend/app/datos/enlace.json`: `luna`, `marte_cercano`, `marte_medio` y `marte`. Cambian con `POST /api/enlace`.
- Cada evento pasa por `retenido` → `en_transito` → `recibido` (llegó a Tierra) y queda `confirmado` cuando vuelve la confirmación (ida y vuelta).
- `GET /api/enlace/latencia` devuelve el perfil vigente, los tiempos reales y simulados y los eventos en tránsito.
- Los retardos son supuestos de diseño y deben verificarse contra fuentes publicadas antes de citarlos.

## Endpoints útiles para el frontend

La lista completa y siempre actual está en [docs/API_REFERENCIA.md](docs/API_REFERENCIA.md) (generada desde el código).

| Endpoint | Para qué |
|---|---|
| `GET /api/historial/{id}?indicador=` | Serie temporal para gráficas |
| `GET /api/explicaciones` y `/{indicador}` | Qué es, por qué se mide, cómo medirlo y qué cambia en el espacio |
| `GET /api/peligros` | Marco de peligros y riesgos del HRP con la cobertura real |
| `GET/PUT /api/preferencias/{id}` | Tono, detalle y recordatorios del asistente (solo su dueño) |
| `POST /api/animo`, `GET /api/animo/{id}` | Ánimo diario, privado |
| `GET /api/demo/comparativa?entorno=&respuesta_tierra_min=` | Línea de tiempo con y sin ORBIT |
| `GET /api/recordatorios` y `/{id}` | Quién tiene la medición vencida, según su nivel y su frecuencia elegida |
| `POST /api/sensores/lectura` y `/lote` | Entrada de dispositivos (origen `sensor`); el lote es todo o nada |
| `POST /api/demo/sensor/{id}?perfil=` | Un dispositivo portátil simulado (estable, deterioro respiratorio o exposición a radiación acumulada) |
| `GET /api/entornos` y `/{clave}` | Entornos con su gravedad y si la estimación de pérdida ósea aplica (solo en microgravedad) |
| `GET /api/racha/{id}` | Racha de días con los 5 signos vitales, sin presión |
| `GET /api/explicaciones/{clave}` | Ahora trae `medidas_nasa` y `senales_a_vigilar` con cita textual y enlace |
| `GET /api/tierra/mensajes` | Vista del centro de control: solo lo que ya llegó, lo urgente primero. Solo lectura, no consume mensajes |
| `GET /api/informe` y `/api/informe/{id}` | Informe exportable (JSON o CSV) con huella de integridad |
| `GET /api/crisis/protocolo`, `POST /api/crisis/aviso-medico` | Protocolo de crisis psicológica / riesgo de autolesión con evaluación de calidad de oxígeno en cabina (`o2_cabina`) y aviso al comandante solo con consentimiento explícito |

## Misión simulada en vivo (para la demo)

Para que la demo no sea manual: `POST /api/demo/simulacion/iniciar` pone a una tripulación a enviar datos sola por el mismo canal que usaría una banda real, con una historia narrada (sube el CO₂, se pierde el enlace, vuelve y sale primero lo urgente). Ver [docs/DEMO_EN_VIVO.md](docs/DEMO_EN_VIVO.md).

## Banda o pulsómetro por Bluetooth

La frecuencia cardíaca puede llegar sola desde un dispositivo BLE que anuncie el servicio estándar; ver [docs/BANDA_BLE.md](docs/BANDA_BLE.md). El puente está probado con una banda simulada. Con una banda real de consumo (IDW26, app Veryfit) se conectó, pero habla un protocolo propio y **no está soportada**; solo funcionarían dispositivos con el servicio estándar.

## Instalable como app (PWA)

La interfaz trae manifiesto y service worker: en un navegador moderno se puede **instalar** y abre aunque el servidor tarde en responder. Funciona en `localhost` o con HTTPS; **por HTTP simple en la red de la cabina el navegador no la instala**, y para eso haría falta TLS (pendiente). El service worker nunca guarda respuestas de `/api`, así que los datos clínicos siempre vienen del servidor. Verificado: el servidor sirve el manifiesto, el service worker y el icono; **no probado** el flujo de instalación en un navegador real.

## IA local (opcional)

Un modelo local sin internet puede explicar una alerta o responder por voz, pero nunca decide el nivel: una crisis la atiende siempre el protocolo escrito y todo texto del modelo se valida y se marca como IA. Ver [docs/IA_LOCAL.md](docs/IA_LOCAL.md).

## Escenarios de demo

```bash
curl -X POST localhost:3000/api/demo/escenarios/hipoxia_eclipse                 # deja el enlace en eclipse
curl -X POST "localhost:3000/api/demo/escenarios/hipoxia_eclipse?reconectar=true"  # y reconecta en el mismo paso
curl -X POST localhost:3000/api/demo/escenarios/co2_colectivo
curl -X POST "localhost:3000/api/demo/sensor/T1?perfil=exposicion_radiacion&ticks=12"  # dosis acumulada: amarillo y luego rojo
curl localhost:3000/api/demo/escenarios                                         # lista de guiones
```

Escriben datos de demostración: en cualquier otro entorno, desactivar con `ORBIT_DEMO_API=0`.

## Desarrollo

```bash
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev            # http://localhost:3000, proxy /api → :8000
cd backend && pytest -q
```

## Prueba offline (checklist manual)

1. Construir el frontend y arrancar el servidor como arriba.
2. Desactivar Wi-Fi y Ethernet.
3. Abrir `http://localhost:3000`; en Monitor registrar SpO₂ 88 (debe salir rojo, prioridad 1).
4. En Enlace activar Modo Eclipse, registrar una lectura normal y otra crítica: quedan retenidas.
5. Escribir una nota en Bienestar y responder el PHQ-2: no aparecen en la cola.
6. Volver a Enlace normal: la prioridad 1 sale primero. Pulsar "Verificar cadena de hash".

Verificado automáticamente: el build no referencia recursos remotos (solo cadenas internas de React),
y el flujo anterior pasa por API contra un servidor único.

## Variables de entorno

Ver `.env.example`. Umbrales marcados como *Supuesto* en el plan requieren validación médica.

## Validación médica

Ver [docs/VALIDACION_MEDICA.md](docs/VALIDACION_MEDICA.md), [docs/DECISIONES_EQUIPO.md](docs/DECISIONES_EQUIPO.md) y `docs/casos_validacion.csv`.

## Estructura

```
backend/app/
  api/            routers HTTP (sistema, lecturas, bienestar, enlace)
  servicios/      casos de uso (registrar lectura, estado, cola y enlace, bienestar)
  repositorios/   acceso a SQLite (todo el SQL) y schema.sql
  dominio/        reglas clínicas puras, catálogo, integridad (hash) y carga de umbrales
  fuentes/        calibración PhysioNet y semilla demo
  datos/          umbrales.json: fuente única de umbrales clínicos
backend/tests/    pruebas pytest
frontend/src/     React + TypeScript
data/             series de calibración (BIDMC) y base local (no se versiona)
docs/             validación médica y casos escenario
scripts/          arranque, E2E, calibración, generador de casos
```

Dependencias entre capas: `api → servicios → repositorios`, y `servicios → dominio`. `dominio` no depende de nada.


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación técnica, registrar las decisiones de arquitectura y mantener la trazabilidad con el código fuente y las fuentes públicas de la NASA, bajo la definición conceptual, revisión y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
