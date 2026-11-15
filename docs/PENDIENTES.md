# Estado y pendientes

Última revisión: sábado 14/11/2026, con `main` en la versión que une backend y frontend. Cierre del envío: **domingo 15/11, 11:59 p. m.** hora del evento local.

## Estado verificado

| Qué | Resultado |
|---|---|
| Pruebas del backend | En verde (`cd backend && .venv/bin/pytest -q`) |
| Pruebas del frontend | En verde (`cd frontend && npm test`) |
| E2E del backend (`scripts/verificar_e2e.sh`) | OK |
| Compilación del frontend (`npm run build`) | OK, sin recursos remotos (sin CDN ni fuentes externas) |
| Servidor real sirviendo el frontend compilado | `GET /` responde, los recursos del `index` cargan y los 24 GET y 5 escrituras probados responden 200 (no se probaron por HTTP los endpoints de crisis, solo con pruebas automáticas) |
| Autenticación activada, servidor real por HTTP | Sin sesión 401; PIN incorrecto 401; diario solo del dueño (médico y comandante 403); solo médico o comandante cambian el enlace; auditoría verificable |
| Seguridad de rutas | Con la autenticación activa, **solo las 11 rutas declaradas públicas** responden sin sesión; lo comprueba una prueba que recorre todas |
| Documentación contra el código | Probada: rutas citadas, referencia de la API, enlaces, variables de entorno y cifras de cobertura deben coincidir con el código |
| Ramas | `frontend-santi` y `dev-frontend` ya están dentro de `main` |

## Qué usa ya la interfaz y qué no

| Ya lo usa | Todavía no lo usa |
|---|---|
| lecturas, estado, historial, explicaciones, peligros, preferencias, latencia, escenarios, diario, tamizajes, ánimo, comparativa, alertas colectivas, acceso con PIN, **recordatorios, vista de Tierra, informe, sensor simulado y protocolo de crisis** | `salud`, `auditoria`, reinicio de PIN y el lote de `sensores` |

## Pendientes, por prioridad

| # | Qué | Quién | Nota |
|---|---|---|---|
| 1 | **Confirmar el origen y la licencia de `astronauta.svg`** o sustituirla por una propia | Frontend | La atribución dice "pendiente de confirmar: parece una imagen de banco de imágenes". El repo es público y el reto exige declarar qué se generó con IA |
| 2 | Completar `docs/SI_DISCLOSURE.md` (puntos marcados `TEAM TO CONFIRM`) y registrarlo en el formulario | Equipo | Regla obligatoria del reto |
| 3 | Demo en inglés: video de 30 s o menos, o 7 diapositivas, en enlace público | Equipo | Si el video es en español, con subtítulos en inglés |
| 4 | Ensayar el demo completo **con el Wi-Fi apagado** en el equipo de la presentación | Equipo | Correr antes `scripts/verificar_e2e.sh` |
| 5 | Validación médica de los umbrales y de los textos del protocolo de crisis | Médico y profesional de salud mental | Es lo más expuesto frente al criterio de Validez |
| 6 | Decidir si el **comandante** debe poder ver los avisos de salud mental | Equipo | Hoy pueden verlos médico y comandante; la interfaz se lo dice al tripulante antes de consentir |

## Hallazgos menores de la última revisión
- Listar los avisos de salud mental **no queda en la auditoría** (crear, revocar y atender sí). Conviene auditarlo.
- `GET /api/salud` es público y muestra nombres de archivos de respaldo y el detalle de un error de arranque. Es de baja sensibilidad; si se prefiere, puede exigir sesión.
- `frontend/docs/FIGURA_HUMANA.md` cita un script `preparar_musculos.py` que no existe en el repo.

## Cerrado en la última ronda
- **Datos simulados etiquetados como simulados:** la misión en vivo, las ráfagas de `/demo/sensor` y los escenarios se guardaban como `sensor` o `manual`. Ahora son `simulado` (se ve en el historial, el informe y el evento a Tierra). Una fuente simulada del frontend debe declarar `"origen": "simulado"`.
- **Medidas de salud con fuente:** `explicaciones` trae `medidas_nasa` y `senales_a_vigilar` con cita textual y enlace de la NASA; donde la NASA no da guía (glucosa, contramedidas de hipoxia) se dice. Los consejos generales nuestros ya no se atribuyen a la NASA.
- **Entornos con gravedad:** `GET /api/entornos`. La estimación de pérdida ósea solo aplica en microgravedad; para gravedad parcial la NASA no da cifra. **El frontend aún no lo usa**: hoy calcula pérdida ósea sin distinguir entorno.
- **Racha de mediciones:** `GET /api/racha/{id}`. El frontend aún no la usa.
- **Falsas alarmas de la línea base:** corregidas con un piso de variación por indicador (supuesto pendiente de validación).

## Para la demo
- **Misión simulada en vivo** (`docs/DEMO_EN_VIVO.md`): corrida real por HTTP verificada; el frontend puede consultarla con `GET /api/demo/simulacion/estado`.
- Un apagón largo acumula muchos eventos de rutina (147 en el apagón simulado). Resumirlos antes de enviar sigue pendiente.

## No verificado (hay que comprobarlo a mano)
- **Banda Aolon (u otra de consumo):** falta saber si trae el servicio estándar de frecuencia cardíaca. Se comprueba en un minuto con `puente_ble.py --escanear` y `--inspeccionar` (ver `docs/BANDA_BLE.md`). Si habla un protocolo propio, queda fuera de lo que se puede prometer.
- **Una banda real:** el puente BLE y el flujo continuo están probados con paquetes simulados, no con hardware. Ver `docs/BANDA_BLE.md`.
- Cómo se ve y se siente la interfaz en el navegador, y el flujo completo con una persona usándola.
- El video, las diapositivas y el formulario de envío.
- Que todos los integrantes estén confirmados en el mismo evento local.
- El flujo de acceso con PIN **en la interfaz** (el backend sí está probado por HTTP).

## Cifras que muestra la interfaz
- **Pérdida ósea de 1 a 1.5 % por mes:** verificada en las páginas oficiales de NASA sobre [campos de gravedad](https://www.nasa.gov/hrp/hazard-gravity-fields/) y [cambios óseos](https://www.nasa.gov/reference/risk-of-spaceflight-induced-bone-changes/). La fuente la da para misiones de 4 a 6 meses y avisa de que en más tiempo no está bien caracterizada; la interfaz limita el cálculo a 6 meses y lo marca como ilustrativo.

## Decisiones abiertas
- **Cómo contar la "IA personalizada":** como personalización por preferencias elegidas por el tripulante, sin vender un modelo que aprende personalidades.
- **Menciones a NASA/HRP:** el reto invita a usar esos recursos y pide explicar cómo se usaron, así que no es un problema por sí mismo.

## Si sobra tiempo en el backend
Tierra que responde con retraso y pérdida de paquetes con reintentos. (Resumir lo rutinario al enviar ya está hecho.)

## Fuera de alcance, declarado como trabajo futuro
Cifrado de la base, TLS en la red de la cabina, sensores y radio reales. El explicador de modelo local ya está integrado de forma opcional, pero requiere instalar y validar un modelo en la estación. Sus protecciones están en [IA_LOCAL.md](IA_LOCAL.md); la lista de frases de crisis necesita revisión profesional.
