# API consumida por el frontend / Frontend API Reference

Base: `/api` (proxy de Vite hacia `http://localhost:8000` en desarrollo; servido directamente por FastAPI en producción).  
Cliente base: [`src/shared/api/client.ts`](../src/shared/api/client.ts).

---

## Seguridad y sistema / Security & System

| Método | Ruta | Feature | Uso / Purpose |
|---|---|---|---|
| GET | `/api/auth/estado` | `seguridad` | Estado de autenticación y si requiere acceso / Auth status |
| POST | `/api/auth/login` | `seguridad` | Inicio de sesión por tripulante y PIN / Crew PIN login |
| POST | `/api/auth/logout` | `seguridad` | Cierre de sesión / Logout |
| GET | `/api/auth/yo` | `seguridad` | Actor autenticado actual / Current authenticated actor |
| POST | `/api/auth/recuperar` | `seguridad` | Solicitud de recuperación de PIN / PIN recovery request |
| POST | `/api/auth/reiniciar-pin/{tid}` | `sistema` | Reinicio de PIN por comandante / Commander PIN reset |
| GET | `/api/auditoria` | `sistema` | Eventos de auditoría / Audit log events |
| GET | `/api/auditoria/verificar` | `sistema` | Verificación de cadena de hashes / Hash-chain integrity check |
| GET | `/api/salud` | `sistema` | Salud de base de datos y respaldos / DB & backup health |
| GET | `/api/umbrales` | `app` | Versión y estado de validación de umbrales / Thresholds version & validation |
| GET | `/api/tripulantes` | `tripulantes`, `sistema` | Lista de tripulantes / Crew list |

## Monitor, cabina, mediciones e historial / Monitor, Cabin, Readings & History

| Método | Ruta | Feature | Uso / Purpose |
|---|---|---|---|
| GET | `/api/indicadores` | `mediciones` | Catálogo de indicadores y rangos / Indicators catalog & ranges |
| POST | `/api/lecturas` | `mediciones` | Registrar lectura manual / Submit manual reading |
| GET | `/api/estado/{tid}` | `monitor` | Estado actual, NEWS2 e indicadores / Current status, NEWS2 & vitals |
| GET | `/api/estado/{tid}/explicacion` | `monitor`, `app` | Explicación clínica local del estado / Local AI status explanation |
| GET | `/api/historial/{tid}` | `monitor`, `historial` | Serie histórica por indicador / Historical time series |
| GET | `/api/alertas/colectivas` | `cabina` | Alertas colectivas de cabina (CO₂) / Collective cabin alerts |
| GET | `/api/recordatorios` | `monitor` | Recordatorios de captura del equipo / Crew capture reminders |
| GET | `/api/recordatorios/{tid}` | `monitor` | Recordatorios del tripulante / Crew member reminders |
| GET | `/api/racha/{tid}` | `monitor`, `banda` | Racha diaria y logros de medición / Measurement streak & milestones |
| GET | `/api/explicaciones` | `monitor` | Catálogo de explicaciones clínicas / Clinical explanations catalog |
| GET | `/api/entornos` | `enlace` | Catálogo de entornos (Luna/Marte) / Environments catalog |
| GET | `/api/peligros` | `peligros` | Marco de peligros NASA HRP / NASA HRP hazards framework |

## Bienestar, asistente Nova y voz / Wellbeing, Nova Assistant & Voice

| Método | Ruta | Feature | Uso / Purpose |
|---|---|---|---|
| POST / GET | `/api/diario`, `/api/diario/{tid}` | `bienestar` | Diario privado local (no entra a la cola) / Local private journal |
| POST | `/api/tamizajes` | `bienestar` | Tamizaje PHQ-2 / PHQ-2 screening |
| POST / GET | `/api/animo`, `/api/animo/{tid}` | `bienestar` | Registro y serie de ánimo diario / Daily mood tracker & series |
| GET / PUT | `/api/preferencias/{tid}` | `bienestar` | Preferencias del asistente / Assistant preferences |
| GET | `/api/crisis/protocolo` | `bienestar` | Protocolo de crisis / Crisis protocol |
| POST / GET | `/api/crisis/aviso-medico`, `/api/crisis/avisos/{tid}` | `bienestar` | Avisos médicos con consentimiento / Consent-based medical alerts |
| POST | `/api/crisis/avisos/{id}/revocar` | `bienestar` | Revocar aviso compartido / Revoke shared alert |
| GET / POST | `/api/crisis/avisos`, `/api/crisis/avisos/{id}/atender` | `sistema` | Revisión y atención de avisos por comandante / Commander alert review |
| GET / PUT | `/api/perfil-ia/{tid}` | `asistente` | Intereses y rasgos personales para Nova / Personal interests & traits |
| GET | `/api/asistente/saludo/{tid}` | `asistente` | Saludo contextual y atajos de Nova / Nova contextual greeting & shortcuts |
| POST | `/api/asistente/chat/{tid}` | `asistente` | Chat privado por texto con Nova / Private text chat with Nova |
| POST | `/api/voz/chat/{tid}` | `voz`, `bienestar`, `monitor`, `app` | Chat por voz bilingüe ES/EN / Bilingual ES/EN voice chat |

## Enlace, Tierra, informes y demo / Link, Earth, Reports & Demo

| Método | Ruta | Feature | Uso / Purpose |
|---|---|---|---|
| GET / POST | `/api/enlace` | `enlace` | Estado del enlace y Modo Eclipse / Link status & Eclipse Mode |
| GET | `/api/enlace/latencia` | `enlace` | Latencia actual del enlace / Current link latency |
| GET | `/api/cola` | `enlace` | Cola priorizada hacia la Tierra / Priority queue to Earth |
| GET | `/api/cola/verificar` | `enlace` | Verificación SHA-256 de la cola / Queue hash-chain verification |
| GET | `/api/tierra/mensajes` | `enlace` | Mensajes recibidos en Tierra / Earth-received messages |
| GET | `/api/informe`, `/api/informe/{tid}` | `enlace` | Descarga de informes (JSON / CSV) / Report downloads |
| GET / POST | `/api/demo/escenarios`, `/api/demo/escenarios/{nombre}` | `enlace` | Escenarios de demostración / Demo scenarios |
| GET | `/api/demo/comparativa` | `enlace` | Comparativa con y sin ORBIT / With vs. without ORBIT comparison |
| POST | `/api/demo/sensor/{tid}` | `enlace` | Inyección de sensor de prueba / Demo sensor injection |
| GET / POST | `/api/demo/simulacion/{estado,iniciar,detener}` | `banda`, `enlace` | Misión simulada en vivo / Live simulated mission |

---

## Justificación del uso de IA / AI Usage Justification

Los contratos de API, umbrales clínicos y reglas de negocio fueron definidos y validados por el equipo; la IA se empleó como apoyo para conectar hooks/componentes en TypeScript y generar pruebas unitarias sobre contratos mockeados. Ver [USO_IA_Y_DOCUMENTACION_FRONTEND.md](./USO_IA_Y_DOCUMENTACION_FRONTEND.md) y [docs/SI_DISCLOSURE.md](../../docs/SI_DISCLOSURE.md).
