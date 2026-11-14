# Figura humana interactiva (SVG)

Elemento visual central del producto: reemplaza al "cerebro de partículas" de la referencia Dala. Es un SVG de cuerpo humano con **zonas clicables** que se colorean según el estado clínico.

Ubicación objetivo: `features/monitor/components/FiguraHumana.tsx` (hoy en `src/components/`).

## Estado actual

Implementación inicial con formas geométricas simples (círculo, rectángulos), 5 zonas, `React.memo`, color por clase CSS. **Aún no es clicable** y no es una silueta humana.

## Zonas e indicadores (mapeo actual en el frontend)

| Zona | Indicadores (backend) |
|---|---|
| Cabeza / SNC | `avpu` |
| Cardiovascular | `presion_sistolica`, `presion_diastolica`, `frecuencia_cardiaca` |
| Respiratorio | `spo2`, `frecuencia_respiratoria` |
| Tronco / Metabólico | `glucosa`, `temperatura` |
| Extremidades | ninguno en el prototipo |

Nivel de una zona = el peor de sus indicadores (`rojo > amarillo > verde`); sin lecturas = `sin_datos`.

## Requisitos de la nueva figura

1. **Silueta humana en SVG** con regiones separadas: cabeza, tórax (corazón/pulmones), abdomen, brazos, piernas.
2. **Click en una zona** → abre el detalle de esa zona (indicadores, niveles, guía). Estado `zonaSeleccionada` en `useZonaSeleccionada`.
3. Color por estado con transición CSS en `fill`; alerta con `@keyframes` sobre `opacity`. Sin filtros SVG pesados (`blur`, `drop-shadow`).
4. Accesibilidad: cada zona con `role="button"`, `tabIndex={0}`, `aria-label` y `<title>`; activable con Enter/Espacio. El estado nunca depende solo del color (badge con texto).
5. `React.memo` para evitar renders por refrescos de fondo.

## Decisión pendiente

El backend no tiene indicadores de brazos o piernas. Opciones:

| Opción | Trade-off |
|---|---|
| A. Brazos/piernas clicables que muestran "sin indicador en el prototipo" | Cumple la demo visual; honesto sobre el alcance |
| B. Asociar a brazos un indicador existente (p. ej. presión arterial) | Más "vivo", pero es un mapeo arbitrario (**Supuesto**) |
| C. Añadir indicadores nuevos en el backend (ejercicio, masa ósea) | Más completo; requiere trabajo y validación de umbrales en backend |

Recomendación: A para la entrega; C si sobra tiempo. Confirmar con el equipo.

## Pendientes

- Obtener o dibujar el SVG de la silueta (verificar licencia si se toma de terceros).
- Definir si las zonas se dibujan como `<path>` por región (recomendado) o con formas simples.
