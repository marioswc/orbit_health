# 05 — Enlace Tierra–Nave, Historial e Informes

## Qué problema había
En misiones a la Luna o Marte la señal tarda en llegar o se corta por completo (apagones). El equipo en la nave necesita ver qué mensajes quedaron retenidos, simular escenarios reales para demostrar la tolerancia a fallos y consultar el historial completo de cada signo vital sin saturar la pantalla.

## Cómo se resolvió
- **Consola de Enlace y tolerancia a apagones ([EnlacePage.tsx](../../src/features/enlace/routes/EnlacePage.tsx), [ConsolaEnlace.tsx](../../src/features/enlace/components/ConsolaEnlace.tsx), commits `905657a`, `b2b942c`):**
  - Muestra en tiempo real si el enlace está activo o en apagón, la latencia según el entorno (órbita, Luna o Marte) y cuántos mensajes están **retenidos**, **en tránsito** o **recibidos**.
  - Permite verificar la integridad de la cola local (`/api/cola/verificar`) para confirmar que ningún evento fue alterado durante un corte.
- **Simulador de misión en vivo ([SimuladorDemo.tsx](../../src/features/enlace/components/SimuladorDemo.tsx), commits `73c01c4`, `f8a3cec`):**
  - Se conectaron botones para **iniciar y detener la misión en vivo**, además de cargar escenarios de prueba y comparar la latencia entre entornos.
- **Vista de Tierra y descarga de informes ([VistaTierra.tsx](../../src/features/enlace/components/VistaTierra.tsx), commit `9f6e98e`):**
  - Muestra los mensajes clínicos que ya llegaron a Tierra y ofrece enlaces directos para descargar el informe de tripulación.
- **Historial en tabla plegable y paginada ([HistorialPage.tsx](../../src/features/historial/routes/HistorialPage.tsx), commits `25b68ba`, `8e99522`, `8573833`):**
  - Reemplazó listas largas difíciles de leer por una tabla ordenada con filas desplegables, gráficas detalladas por indicador y paginación para revisar mediciones pasadas con fluidez.


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación de frontend, arquitectura de interfaz y componentes, bajo el diseño visual, criterio de experiencia de usuario y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
