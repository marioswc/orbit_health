# 06 — Navegación, Estilo, Idiomas y Soporte Offline (PWA)

## Qué problema había
A medida que crecieron las funciones (Monitor, Banda, Historial, Bienestar, Asistente, Riesgos, Enlace, Sistema), la interfaz necesitaba mantenerse limpia, rápida en equipos modestos, bilingüe para jueces de habla inglesa e instalable para funcionar sin depender de internet.

## Cómo se resolvió
- **Menú lateral animado y barra adaptable ([BarraLateral.tsx](../../src/app/BarraLateral.tsx), [layout.css](../../src/shared/styles/layout.css), commits `901bc30`, `64c209f`, `b180c0e`):**
  - Menú lateral colapsable con indicador deslizante que en teléfonos se transforma en barra inferior.
  - Se retiró una etiqueta flotante (`::after`) que se superponía sobre los títulos cuando la barra estaba colapsada, manteniendo la accesibilidad con `aria-label` y `title`.
- **Nuevo logo en silueta ([Logo.tsx](../../src/shared/components/Logo.tsx), commit `b180c0e`):**
  - Se integró el isotipo de **ORBIT Health** (esquinas HUD, órbita y trazo cardíaco) sin recuadro de fondo, adaptándose automáticamente a modo claro y modo oscuro.
- **Idiomas Español / Inglés ([i18n](../../src/i18n/index.ts), commits `901bc30`, `feef45a`):**
  - Toda la interfaz soporta cambio inmediato entre **ES** y **EN** con un modal de transición limpio y archivos de traducción divididos por módulo.
- **Sistema visual consistente y rendimiento ([ESTILO_PLATAFORMA.md](../ESTILO_PLATAFORMA.md), commit `c9f1081`):**
  - Paleta casi acromática con modo claro/oscuro, paneles *liquid glass*, semáforo clínico siempre acompañado de texto y detección de rendimiento reducido para desactivar efectos pesados si hace falta.
- **PWA mínima offline ([manifest.webmanifest](../../public/manifest.webmanifest), [sw.js](../../public/sw.js), commit `fc7de22`):**
  - Manifiesto e ícono propios para instalar la app y *service worker* que guarda los archivos estáticos de la interfaz **sin cachear nunca `/api`**, garantizando que los datos clínicos siempre vengan frescos del servidor local.


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación de frontend, arquitectura de interfaz y componentes, bajo el diseño visual, criterio de experiencia de usuario y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
