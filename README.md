# ORBIT Health

Apoyo a la decisión clínica para tripulaciones con comunicación degradada. Funciona 100 % local.
English summary for judges: [docs/PROJECT_SUMMARY_EN.md](docs/PROJECT_SUMMARY_EN.md). Use of SI tools (required by the challenge): [docs/SI_DISCLOSURE.md](docs/SI_DISCLOSURE.md).

Plan completo: [PLAN_DE_DESARROLLO.md](backend/docs/PLAN_DE_DESARROLLO.md).

## Producción local (un solo servidor, sin internet)

```bash
cp .env.example .env
cd frontend && npm install && npm run build && cd ..
cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
set -a; . ../.env; set +a
uvicorn app.main:app --port 3000      # sirve API y frontend en http://localhost:3000
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

## Escenarios de demo

```bash
curl -X POST localhost:3000/api/demo/escenarios/hipoxia_eclipse                 # deja el enlace en eclipse
curl -X POST "localhost:3000/api/demo/escenarios/hipoxia_eclipse?reconectar=true"  # y reconecta en el mismo paso
curl -X POST localhost:3000/api/demo/escenarios/co2_colectivo
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
