# Astronauta interactivo

Pantalla principal del Monitor: un astronauta de frente al centro, zonas a la izquierda y detalle a la derecha. Elegir una zona acerca la cámara, revela una capa anatómica con la región a color y muestra una línea de llamada hacia el panel.

Ubicación: `features/monitor/` — `components/FiguraHumana.tsx`, `components/ArteAstronauta.tsx`, `components/DetalleZona.tsx`, `zonas.ts`, `zonasPaths.ts`, `assets/`.

## Capas (todas SVG, alineadas en las mismas coordenadas)

| Capa | Archivo | Origen |
|---|---|---|
| Traje | `astronauta.svg` | Vectorización con curvas de la ilustración de referencia del equipo. **Licencia por confirmar** (parece de banco de imágenes) |
| Músculo | `musculos.svg` | "Muscles front and back.svg" (Wikimedia Commons; OpenStax, Tomáš Kebert y umimeto.org), recortada a la vista frontal con `scripts/preparar_musculos.py`. **CC BY-SA 4.0**: exige atribución y que las adaptaciones conserven la misma licencia |
| Hueso | `esqueleto.svg` | Wikimedia Commons, dominio público (LadyofHats) |
| Órganos | `organos.svg` | Wikimedia Commons, dominio público (LadyofHats) |

Detalle y atribuciones en `assets/ATRIBUCION.md`. Las capas se alinean por el centro de la cabeza (casco) y por los pies (botas). En cada capa activa, la región de la zona elegida se ve a todo color y el resto apagado (`REGIONES` en `ArteAstronauta.tsx`).

## Zonas

| Zona | Indicadores (backend) | Capa inicial |
|---|---|---|
| Cabeza / SNC | `avpu` | Órganos |
| Respiratorio | `spo2`, `frecuencia_respiratoria` | Órganos |
| Cardiovascular | `presion_sistolica`, `presion_diastolica`, `frecuencia_cardiaca` | Órganos |
| Tronco / Metabólico | `glucosa`, `temperatura` | Órganos |
| Brazos | ninguno en el prototipo | Músculo |
| Piernas | ninguno en el prototipo | Músculo |

Nivel de zona = el peor de sus indicadores; sin lecturas = `sin_datos`. Los textos de efectos salen de los videos de NASA HRP (*Hazards of Human Spaceflight*) y se presentan como efectos generales de la misión, no como diagnóstico. En la capa Hueso de brazos y piernas hay una línea de tiempo (0–6 meses) que estima la **pérdida** de densidad ósea con una tasa constante de ≈1–1.5 % mensual (NASA HRP); es un cálculo simple del equipo, ilustrativo. La microgravedad disminuye la densidad ósea; no la aumenta.

## Interacción

- Cada zona es clicable en el dibujo (contorno del traje) y desde la lista; se puede usar el teclado.
- `?zona=brazos&capa=musculo` abre la vista directamente (útil para la demo).
- Inclinación suave con el cursor, barrido de escaneo, onda y brillo al elegir; todo respeta `prefers-reduced-motion`.

## Limitaciones

- Una sola postura de frente: no se consiguió otra imagen utilizable.
- Las capas de anatomía no coinciden exactamente con la postura del traje (brazos).
- Pendiente: confirmar la redacción de los efectos y la licencia del traje.
