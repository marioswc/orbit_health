# Avance del frontend — rama `frontend-santi`

Registro del trabajo de interfaz en curso. Rama creada desde `frontend` (2026-11-14). Los cambios siguen **sin commitear**.

## Resumen

| Área | Estado | Archivos clave |
|---|---|---|
| Header fijo (sticky) | Hecho | `styles.css`, `escenario.css` |
| Fondo espacial con estrellas y estrellas fugaces | Hecho | `shared/components/FondoEstrellas.tsx`, `App.tsx`, `styles.css` |
| Escenario del astronauta más grande | Hecho | `escenario.css` |
| Tarjetas separadas en vez de una caja única | Hecho | `MonitorPage.tsx`, `escenario.css` |
| Tema claro/oscuro, fuentes locales, módulos CSS | Previo a esta sesión (ver diff) | `tokens.css`, `useTema.ts`, `index.html`, `main.tsx` |
| Verificación visual y `pnpm build` | **Pendiente** | — |

## Cambios de esta sesión

### 1. Header fijo
- `.barra` pasa a `position: sticky; top: 0; z-index: 20`, con fondo semitransparente (80 % del color base) y `backdrop-filter: blur(12px)`.
- El panel izquierdo del escenario (`.lado.izq`, también sticky) sube su `top` a `calc(24px + 64px)` para no quedar bajo el header.
- **Supuesto:** "que el header se baje" se interpretó como "que acompañe al hacer scroll". Confirmar con quien lo pidió.

### 2. Fondo de estrellas (`FondoEstrellas.tsx`)
- Canvas 2D `position: fixed` detrás de toda la app (`z-index: -1`, `pointer-events: none`, `aria-hidden`). Sin dependencias.
- `body` queda con fondo transparente; el color base vive en `html`.
- **Estrellas:** hasta 260 (según área), quietas, con parpadeo y parallax leve con el scroll (las cercanas se mueven más).
- **Estrellas fugaces:** una cada 1.5–5 s, máximo 3 simultáneas, caen en diagonal hacia abajo-izquierda con cola degradada.
- **Temas:** oscuro = blanco; claro = índigo `rgb(38,52,140)` con fugaces en `#0447ff`. El tema se lee de `data-theme` en `<html>` con un `MutationObserver`.
- **Accesibilidad:** con `prefers-reduced-motion` solo se dibujan estrellas estáticas, sin fugaces ni parpadeo.
- **Limitación conocida:** en tema claro el fondo sigue siendo crema, así que el efecto es de "estrellas sobre papel", no de espacio profundo.

### 3. Escenario del astronauta
- `.plataforma`: se quitó el límite de 440 px de ancho; alto `min(100vh − 120px, 900px)`, mínimo 600 px. El SVG escala solo por su `viewBox`.
- Columnas: `210–240px | 1fr | 300–360px`.

### 4. Tarjetas separadas
- Se eliminó la caja contenedora de `.escenario` (fondo, radio y padding).
- Columna izquierda en tres tarjetas `.panel`: **Zonas**, **Capas** y **Estados** (leyenda). Cambio de marcado en `MonitorPage.tsx`.
- Detalle de zona (`.lado.der`) y astronauta (`.plataforma`) también son tarjetas independientes.
- Estilo común: fondo semitransparente (82 %), `backdrop-filter`, borde 1 px `--color-stone`, radio 20 px. Las estrellas se ven a través.
- ≤ 1100 px el escenario sigue apilándose en una columna.

## Pendiente / siguientes pasos

| # | Tarea | Nota |
|---|---|---|
| 1 | Revisar visualmente en navegador (tema claro y oscuro, móvil) | No se ha corrido la app tras estos cambios |
| 2 | Correr `pnpm build` (`tsc --noEmit`) | Sin verificar |
| 3 | Decidir si el tema claro usa fondo oscuro tipo espacio | Opción A: dejar crema. Opción B: fondo oscuro con textos claros (más trabajo, mejor efecto) |
| 4 | Decidir tamaño final del astronauta | Opción: ampliar `--page-max-width` (hoy 1280 px) o reducir paneles laterales |
| 5 | Header en móvil (≤ 900 px) | Hace wrap a varias filas y, al ser sticky, ocupa mucha altura; evaluar dejarlo estático ahí |
| 6 | Colorear la figura con el estado `GET /api/alertas/colectivas` | El frontend aún no usa este endpoint (ver `API.md`) |

## Reglas de trabajo vigentes
- No hacer commit ni push sin indicación explícita del responsable.
- Lo marcado como **Supuesto** requiere revisión del equipo.
- Documentación relacionada: [ARQUITECTURA.md](./ARQUITECTURA.md), [DISENO.md](./DISENO.md), [FIGURA_HUMANA.md](./FIGURA_HUMANA.md), [API.md](./API.md).
