# Documentación del Frontend y Uso de IA — ORBIT Health

Este documento resume la arquitectura actual del frontend, las decisiones de producto/diseño tomadas por el equipo y la declaración transparente del uso de herramientas de IA, como complemento a [docs/SI_DISCLOSURE.md](../../docs/SI_DISCLOSURE.md).

---

## 1. Propósito y enfoque del Frontend

El frontend de **ORBIT Health** es una interfaz operativa de monitoreo biomédico y bienestar para tripulaciones espaciales, diseñada bajo el principio de **"aplicación de operación, no landing"** ([ESTILO_PLATAFORMA.md](./ESTILO_PLATAFORMA.md)):

- **Casi acromático**: superficies cálidas en modo claro (`#fdfcfc` / `#f5f3f1`) y oscuro (`#121110` / `#1c1a18`), con efecto *liquid glass* en barra lateral y cabecera.
- **Semáforo clínico funcional**: los colores `verde`, `amarillo`, `rojo` y `sin datos` se reservan para estado clínico y **siempre van acompañados de etiqueta de texto** para accesibilidad.
- **Acento HUD**: azul técnico (`#0447ff` en claro / `#6f95ff` en oscuro) para foco anatómico y telemetría.
- **Tipografía**: `Inter` para interfaz y titulares; `Geist Mono` para métricas, rótulos técnicos y trazabilidad.

---

## 2. Mapa de vistas y módulos (`frontend/src/features/`)

La aplicación se organiza por *features* independientes dentro de `frontend/src/features/` y se orquesta desde [App.tsx](../src/app/App.tsx) y [BarraLateral.tsx](../src/app/BarraLateral.tsx):

| Vista | Ruta / Componente principal | Función principal |
|---|---|---|
| **Monitor** | [MonitorPage.tsx](../src/features/monitor/routes/MonitorPage.tsx) | Tablero clínico principal: anillo NEWS2, pulso cardíaco, signos vitales, gráfica de tendencia, selector de entorno (`GET /api/entornos`), figura anatómica por zonas (`DetalleZona.tsx`), recordatorios (`RecordatorioCaptura.tsx`) y racha (`RachaMediciones.tsx`). |
| **Banda** | [BandaPage.tsx](../src/features/banda/routes/BandaPage.tsx) | Visualización de lecturas de la banda/reloj de actigrafía (`RelojBanda.tsx`) y estado de simulación/sensores. |
| **Historial** | [HistorialPage.tsx](../src/features/historial/routes/HistorialPage.tsx) | Tabla histórica de indicadores y mediciones del tripulante seleccionado. |
| **Bienestar** | [BienestarPage.tsx](../src/features/bienestar/routes/BienestarPage.tsx) | Diario de bienestar y tamizaje con almacenamiento separado de la telemetría general. |
| **Riesgos** | [RiesgosPage.tsx](../src/features/peligros/routes/RiesgosPage.tsx) | Consulta de riesgos y peligros operativos. |
| **Enlace** | [EnlacePage.tsx](../src/features/enlace/routes/EnlacePage.tsx) | Estado del canal Tierra–nave, cola de mensajes en apagón y controles de simulación en vivo ([SimuladorDemo.tsx](../src/features/enlace/components/SimuladorDemo.tsx)). |
| **Sistema** | [SistemaPage.tsx](../src/features/sistema/routes/SistemaPage.tsx) | Estado técnico y configuración de la plataforma. |

---

## 3. Decisiones de producto y diseño tomadas por el equipo

Las siguientes decisiones responden a criterios de UX, flujo operativo y rigor científico definidos por el equipo:

1. **Prioridad a sensores sobre captura manual**: se eliminó de [App.tsx](../src/app/App.tsx) el botón flotante y el cajón de *Captura manual* para que la interfaz refleje un flujo continuo alimentado por sensores/banda y simulación de misión, evitando fricción manual innecesaria.
2. **Estimación ósea condicionada al entorno**: en [DetalleZona.tsx](../src/features/monitor/components/DetalleZona.tsx), el cálculo ilustrativo de pérdida ósea (1–1.5 % mensual) solo se muestra cuando el entorno seleccionado tiene microgravedad; en entornos como Luna, Marte o rover se muestra únicamente la nota informativa correspondiente.
3. **Identidad visual limpia en barra lateral**:
   - [Logo.tsx](../src/shared/components/Logo.tsx) utiliza únicamente la silueta SVG (esquinas HUD, órbita y trazo cardíaco) con `currentColor` para adaptarse automáticamente a modo claro y oscuro sin recuadros de fondo.
   - Se eliminó la píldora flotante `::after` en la barra colapsada ([layout.css](../src/shared/styles/styles.css)) para evitar que tape el encabezado de las vistas, conservando `aria-label` y `title` nativo.

---

## 4. Declaración y justificación del uso de IA en el Frontend

De acuerdo con las reglas del **NASA Space Apps Challenge**, la IA se utilizó como **herramienta de apoyo técnico** para acelerar implementación, pruebas e integración, nunca para sustituir el criterio de diseño ni la validación del equipo.

### Qué decidió el equipo (sin IA)
- La arquitectura visual del tablero, la experiencia de navegación por vistas y el concepto de monitoreo centrado en el astronauta.
- Las reglas de UX: eliminar la captura manual en favor de sensores/banda, mantener la separación de datos de bienestar y exigir trazabilidad visible en las recomendaciones.

### Cómo se usó la IA y cómo se validó

| Área | Apoyo de la IA | Validación y control humano |
|---|---|---|
| **Integración con API y hooks** | Implementación de hooks y componentes (`useEntornos`, `RachaMediciones`, `SimuladorDemo`, `ExplicacionIndicador`) | Revisión de contratos con el backend, pruebas manuales en navegador y ajuste de textos/estados |
| **UI, estilos y SVG** | Adaptación a JSX y limpieza de fondo del isotipo SVG en [Logo.tsx](../src/shared/components/Logo.tsx); ajustes de CSS en [layout.css](../src/shared/styles/styles.css) | Definición del concepto visual de marca, revisión en modo claro/oscuro y decisión final de layout |
| **Integración Git** | Resolución de conflictos de merge entre ramas de frontend y backend (`MonitorPage.tsx`) | Verificación de que no se perdieran funcionalidades de ningún integrante del equipo |
| **Pruebas y verificación** | Generación y actualización de pruebas unitarias con Vitest | Ejecución real de `tsc --noEmit` y suites de Vitest tras cada cambio |

### Puntos por confirmar antes de la entrega final
- **[POR CONFIRMAR]** Listar explícitamente las herramientas de IA utilizadas por cada integrante de frontend (por ejemplo: asistente en IDE / generación de boceto SVG del logo).
- **[POR CONFIRMAR]** Completar el origen y licencia de la ilustración anatómica (`astronauta.svg`) en `frontend/src/features/monitor/assets/ATRIBUCION.md` y en [docs/SI_DISCLOSURE.md](../../docs/SI_DISCLOSURE.md).

---

## 5. Verificación técnica

Comandos de verificación ejecutados sobre el código actual del frontend:

- **Comprobación de tipos TypeScript** (`0` errores):
  ```powershell
  cd frontend
  node node_modules/typescript/bin/tsc --noEmit
  ```
- **Pruebas unitarias verificadas** (`7` archivos, `21` pruebas pasando):
  ```powershell
  cd frontend
  node node_modules/vitest/vitest.mjs run `
    src/app/__tests__/app.test.tsx `
    src/features/banda/__tests__/RelojBanda.test.tsx `
    src/features/monitor/__tests__/DetalleZona.test.tsx `
    src/features/monitor/__tests__/RachaMediciones.test.tsx `
    src/features/monitor/__tests__/RecordatorioCaptura.test.tsx `
    src/features/enlace/__tests__/SimuladorDemo.test.tsx `
    src/features/enlace/__tests__/VistaTierra.test.tsx
  ```
- **Servidor de desarrollo**:
  ```powershell
  cd frontend
  pnpm dev
  ```


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación de frontend, arquitectura de interfaz y componentes, bajo el diseño visual, criterio de experiencia de usuario y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
