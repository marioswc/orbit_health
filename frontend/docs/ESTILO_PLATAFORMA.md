# Estilo de la plataforma — ORBIT Health

Sistema de diseño **vigente** del frontend. Sustituye al de [DISENO.md](./DISENO.md) (referencia Dala, descartada). Fuente de verdad en código: [tokens.css](../src/shared/styles/styles.css), [styles.css](../src/shared/styles/styles.css), [componentes.css](../src/shared/styles/styles.css), [escenario.css](../src/shared/styles/styles.css), [animaciones.css](../src/shared/styles/styles.css).

**Resumen:** aplicación de monitoreo (modo *operar*, no landing). Base ElevenLabs (papel crema, tinta negra, tipografía ligera, botones píldora) + modo oscuro + **liquid glass** gris translúcido en paneles + HUD azul alrededor del astronauta. El color se reserva para el semáforo clínico.

## 1. Principios

| Principio | Qué significa |
|---|---|
| Aplicación, no landing | Densidad media, paneles, controles reconocibles; sin héroes ni decoración gratuita |
| Casi acromático | Superficies cálidas y tinta; el color solo comunica estado o foco (HUD) |
| Estado nunca solo con color | Semáforo siempre acompañado de texto (`verde`, `amarillo`, `rojo`, `sin datos`) |
| Movimiento con propósito | Entradas escalonadas, trazado de flechas, pulso en estados críticos; todo respeta `prefers-reduced-motion` |
| Rendimiento | Solo `transform`/`opacity` en animaciones; sin sombras ni filtros pesados en elementos que se mueven |

## 2. Tokens

### Superficies y texto
| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `--color-eggshell` | `#fdfcfc` | `#121110` | Fondo de página, controles |
| `--color-warm-taupe` | `#f5f3f1` | `#1c1a18` | Tarjetas |
| `--color-stone` | `#ebe8e4` | `#2c2a27` | Bordes, divisores |
| `--color-ink` | `#000000` | `#fdfcfc` | Texto principal, botón activo |
| `--color-graphite` | `#44403b` | `#d6d1ca` | Texto secundario fuerte |
| `--color-smoke` | `#777169` | `#a59f97` | Texto secundario |
| `--color-ash` | `#a59f97` | `#7d776f` | Placeholder, deshabilitado |
| `--color-border-button` | `#e5e5e5` | `#3a3733` | Borde de controles |

### Semáforo clínico (excepción funcional)
| Token | Claro | Oscuro |
|---|---|---|
| `--estado-verde` | `#16a34a` | `#34d399` |
| `--estado-amarillo` | `#d99a00` | `#fbbf24` |
| `--estado-rojo` | `#dc2f1a` | `#ff6b57` |
| `--estado-sin-datos` | `#a59f97` | `#a59f97` |

> **Supuesto:** la guía base es acromática; el equipo añadió el semáforo porque el estado clínico lo requiere. Va siempre con texto.

### HUD (foco y astronauta)
`--hud` = `#0447ff` (claro) / `#6f95ff` (oscuro): marco de esquinas, barrido, zona seleccionada, **flechas**. `--suit`, `--ink`, `--bone` pintan el dibujo del astronauta.

### Tipografía
| Rol | Fuente | Tamaño / peso |
|---|---|---|
| Titulares | Inter Variable (sustituye a Waldenburg, comercial) | 48 px / 300, tracking −0.96 px |
| H2 | Inter | 18 px / 500 |
| Cuerpo | Inter | 14 px / 400 (`--text-body-sm`), 16 px para texto largo |
| Etiquetas, datos, fuentes | Geist Mono Variable | 12 px, mayúsculas con tracking en rótulos de panel |

Escala: 12 · 14 · 16 · 18 · 20 · 32 · 36 · 48 px.

### Espaciado, radios, anchos
- Espaciado: 4 · 8 · 12 · 16 · 20 · 24 · 32 · 48 · 64 px (`--spacing-*`).
- Radios: input y selector 14–16 px · lista del selector 20 px (opciones 12 px) · segmentado 22 px · card 20 px · card grande 24 px · píldora 9999 px. Los controles son redondeados, no cuadrados.
- Ancho máximo de página: 1280 px.

### Movimiento
`--ease-out: cubic-bezier(0.16, 1, 0.3, 1)`. Duraciones 150–300 ms en controles; 550–850 ms en entradas y cámara.

## 3. Modo oscuro
Se activa con `data-theme="dark"` en `<html>`. `index.html` lo fija antes de pintar (sin parpadeo), `useTema` lo alterna y lo guarda en `localStorage` (clave `orbit-tema`, con `try/catch`). Al cambiar, la clase `cambiando-tema` anima solo los bloques grandes (no todos los nodos).

## 4. Liquid glass
Vidrio gris translúcido tipo Apple en la barra superior y los paneles laterales (`.cristal`, `.barra`, `.panel`, `.lado.der`).

| Capa | Receta |
|---|---|
| Fondo | `--glass-bg` (gris translúcido) + degradado de brillo `--glass-sheen` a 135° |
| Desenfoque | `backdrop-filter: blur(22px) saturate(170%)` |
| Borde | `--glass-edge` 1 px + luz interior superior (`inset 0 1px`) y línea inferior `--glass-line` |
| Profundidad | `--glass-shadow` suave (no se usa en elementos animados) |
| Soporte | `@supports not (backdrop-filter)`: cae a `--color-warm-taupe` opaco |
| Luz ambiente | `body::before` fijo con dos gradientes radiales para que el vidrio tenga algo que refractar |

Reglas: máximo 4 superficies con `backdrop-filter` a la vez; **no** aplicarlo al escenario del astronauta (área grande, se redibuja con la cámara).

## 5. Componentes

| Componente | Descripción |
|---|---|
| Botón | Píldora, borde `--color-border-button`, 40 px de alto mínimo; activo = fondo `--color-ink` con texto invertido |
| `.tab` (zona) | Botón con punto de estado; activo invertido |
| Selector | Combobox/listbox propio ([Selector.tsx](../src/shared/components/Selector.tsx)): bordes redondeados, teclado completo (flechas, Home/End, Enter, Escape) |
| Segmentado | Radiogroup de opciones excluyentes ([Segmentado.tsx](../src/shared/components/Segmentado.tsx)): entorno y canal del enlace, respuestas del tamizaje (variante `rejilla`) |
| Drawer | Panel deslizante modal ([Drawer.tsx](../src/shared/components/Drawer.tsx)): foco atrapado, Escape y clic fuera cierran, devuelve el foco. Aloja la **captura manual** |
| Encabezado de página | Rótulo mono + título + descripción + estado a la derecha ([EncabezadoPagina.tsx](../src/shared/components/EncabezadoPagina.tsx)) |
| Chip de indicador | Tira bajo el titular del Monitor: nombre mono, valor grande, badge de nivel y acento de color a la izquierda |
| `.badge` | Píldora con punto de color + texto en mayúsculas |
| Tarjeta | `--color-warm-taupe`, radio 20 px, sin borde ni sombra |
| Panel de cristal | Ver sección 4 |
| Contador | Número que cuenta en 600 ms (salta con reduced-motion) |
| Esqueleto | Bloque con brillo desplazándose mientras carga |

## 5b. Estructura de la aplicación
- **Cabecera de ancho completo** (vidrio, pegada arriba): marca a la izquierda, **vistas al centro** (Monitor · Bienestar · Enlace, control segmentado oscuro), a la derecha **Captura manual** (botón primario), selector de tripulante y tema. Con menos de 800 px las vistas pasan a una segunda fila centrada; con menos de 480 px quedan solo los iconos.
- **Captura manual** vive en el Drawer (se abre desde la cabecera o desde el aviso "Registrar una medición" cuando no hay lecturas), no en una tarjeta al final.
- **Indicadores** son una tira de chips arriba del escenario.
- **Tierra:** foto real (fotografía "Blue Marble" del Apollo 17, NASA, dominio público; ver [ATRIBUCION.md](../src/features/monitor/assets/ATRIBUCION.md)) fija en la parte baja de la pantalla, **estática**, media esfera visible, detrás del contenido y sin recortes (el brillo no se corta). Las tarjetas sobre ella usan 93 % de opacidad para conservar contraste.
- **Bienestar:** diario con línea de tiempo y estado vacío; tamizaje con respuestas segmentadas y medidor 0–6.
- **Enlace:** estado del canal, tres contadores (retenidos / en tránsito / recibidos), controles segmentados, columnas por prioridad con acento rojo/amarillo/verde e integridad de la cola.
- **URL de ensayo:** `?vista=enlace`, `?captura=1`, `?tema=light|dark`, `?zona=…&capa=…&zoom=0`.

## 6. Escenario del astronauta
Layout de tres columnas: zonas/capas/estados · astronauta · detalle (una columna bajo 1100 px, astronauta primero).

- **Capas:** Traje · Músculo · Hueso · Órganos. Las de anatomía se descargan al usarse (o en tiempo ocioso) y se muestran como `<img>` compuestas en GPU.
- **Zonas:** cabeza/SNC, respiratorio, cardiovascular, tronco/metabólico, brazos, piernas; clic o teclado (Enter/Espacio). Relleno según semáforo; contorno punteado al pasar el cursor; azul HUD al seleccionar.
- **Cámara:** al elegir una zona se acerca (zoom 2.2–2.3×) y solo la región de la zona queda a color (máscara radial suave); el resto se apaga.
- **Flechas:** cada capa de anatomía nombra sus estructuras (p. ej. Cerebro, Pulmón, Corazón, Riñones; Pectoral, Bíceps; Cráneo, Costillas…). Etiqueta fuera de la silueta, línea que se traza en 0.7 s, punta de flecha y texto con halo para legibilidad; al acercar solo se muestran las de la zona. Coordenadas en [etiquetas.ts](../src/features/monitor/etiquetas.ts).
- **HUD:** esquinas azules, rótulo de capa en mono, barrido de luz al cambiar de zona/capa, inclinación 3D suave con el cursor (una actualización por fotograma).
- **Fondo:** campo de estrellas en canvas con estrellas fugaces y paralaje con el scroll.
- **Pérdida ósea:** control de 0–6 meses; el hueso se aclara. Texto "1–1.5 % por mes" (NASA HRP, cálculo ilustrativo del equipo).

## 7. Movimiento (catálogo)
| Efecto | Dónde | Propiedades |
|---|---|---|
| Entrada escalonada | `.vista > *`, filas `.item` | `transform`, `opacity` |
| Revelado con desenfoque | `h1` al cambiar de estado | `filter`, `opacity` (solo en el titular) |
| Flotación | `.lienzo` (7 s) | `transform` |
| Pulso | zona roja, punto amarillo/rojo, badge | `opacity`, `transform` |
| Trazado de flecha | `.flecha-linea` | `stroke-dashoffset` |
| Cámara | `.camara` (0.85 s) | `transform` |
| Giro de icono | cambio de tema | `transform`, `opacity` |

`prefers-reduced-motion: reduce` desactiva animaciones y transiciones en toda la app.

## 8. Accesibilidad
- Objetivos de 40 px o más; foco visible (`:focus-visible`, 2 px de tinta).
- Zonas del cuerpo con `role="button"`, `aria-pressed` y `aria-label` con el estado ("Respiratorio: rojo").
- Región en vivo en el panel de detalle (`aria-live="polite"`).
- Contraste: texto sobre cristal usa `--color-ink`/`--color-graphite`; las etiquetas de flecha llevan halo del color de fondo.
- **Pendiente de verificar:** contraste medido con herramienta en modo claro sobre cristal.

## 9. Rendimiento (decisiones de estilo)
SVG optimizados con svgo (de ≈1.3 MB a ≈0.5 MB; presupuesto verificado por test), capas como `<img>`, sin `drop-shadow` en zonas, transiciones de tema acotadas, carga perezosa de vistas (Bienestar, Enlace), consultas del enlace en pausa con la pestaña oculta, estrellas de fondo a ~30 fps (170 máx.), Tierra como imagen estática (cero animación), CSS muerto eliminado. Detalle en los tests de [presupuesto.test.ts](../src/features/monitor/__tests__/presupuesto.test.ts).

## 10. Licencias del arte
| Archivo | Licencia |
|---|---|
| `musculos.webp` | Licencia pendiente (imagen con marca de agua de banco de imágenes) |
| `organos.webp` | Licencia pendiente (procedencia sin verificar) |
| `astronauta.svg` | **Sin confirmar** (posible banco de imágenes): resolver antes de publicar |

Detalle y créditos en [ATRIBUCION.md](../src/features/monitor/assets/ATRIBUCION.md).
