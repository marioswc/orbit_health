# 01 — Monitor y Entornos Espaciales

## Qué problema había
Un tablero médico tradicional muestra muchos números sueltos que cuesta leer rápido en una emergencia, y además no distingue en qué parte del viaje está el astronauta (por ejemplo, la pérdida de hueso de 1–1.5 % mensual aplica en microgravedad, pero no en la Luna o Marte).

## Cómo se resolvió
- **Tablero unificado ([MonitorPage.tsx](../../src/features/monitor/routes/MonitorPage.tsx), commit `8e99522`):**
  - Se organizó la pantalla en tres áreas claras: a la izquierda los indicadores clave (anillo de puntaje clínico **NEWS2**, pulso cardíaco, estado de cabina y gráfica de tendencia); al centro el detalle de la zona elegida, la lista de signos vitales y las acciones sugeridas; y a la derecha el **astronauta interactivo**.
  - Al tocar cualquier parte del cuerpo (cabeza, respiratorio, cardiovascular, tronco, brazos o piernas) o cambiar de capa (*Traje, Músculo, Hueso, Órganos*), la vista hace zoom en esa zona y muestra solo sus datos relevantes.
- **Entornos con gravedad ([useEntornos.ts](../../src/features/monitor/hooks/useEntornos.ts), [DetalleZona.tsx](../../src/features/monitor/components/DetalleZona.tsx), commit `73c01c4`):**
  - Se agregó un selector de entorno conectado al backend (`GET /api/entornos`).
  - El control de pérdida ósea solo aparece cuando el entorno tiene microgravedad; en Luna, Marte o rover se oculta el cálculo y se muestra la nota explicativa real.
- **Explicaciones con respaldo NASA ([ExplicacionIndicador.tsx](../../src/features/monitor/components/ExplicacionIndicador.tsx), commit `73c01c4`):**
  - Cada indicador muestra qué señales vigilar, medidas recomendadas con su cita textual y enlace a la fuente oficial de la NASA, o indica con transparencia cuando la fuente no da una guía específica.
- **Recordatorios y racha sin presión ([RecordatorioCaptura.tsx](../../src/features/monitor/components/RecordatorioCaptura.tsx), [RachaMediciones.tsx](../../src/features/monitor/components/RachaMediciones.tsx), commits `9f6e98e`, `73c01c4`):**
  - Se muestra cuándo toca la siguiente medición según el estado del tripulante y cuántos días seguidos lleva monitoreándose (sin castigos ni alertas agresivas si el día aún está en curso).
- **Mejor rendimiento al cargar (commit `3ab9737`):**
  - Se redujeron peticiones repetidas al arrancar y se evitaron recálculos innecesarios de diseño en pantalla.


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación de frontend, arquitectura de interfaz y componentes, bajo el diseño visual, criterio de experiencia de usuario y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
