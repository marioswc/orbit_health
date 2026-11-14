> **Reemplazado.** Este sistema de diseño (referencia Dala/ElevenLabs inicial) ya no es el vigente. Usar [ESTILO_PLATAFORMA.md](./ESTILO_PLATAFORMA.md). Se conserva como historial.

# Sistema de diseño — referencia "ElevenLabs" adaptada a ORBIT Health

Papel crema, tinta negra, titulares de peso ligero y superficies planas. Es una **aplicación** (modo operar), no una landing: densidad cómoda, componentes conocidos y movimiento con propósito. Tokens en `src/shared/styles/tokens.css`; estilos en `styles.css`.

## Colores

| Token | Valor | Uso |
|---|---|---|
| `--color-eggshell` | `#fdfcfc` | Fondo de página, controles |
| `--color-warm-taupe` | `#f5f3f1` | Tarjetas y bandas |
| `--color-stone` | `#ebe8e4` | Líneas finas, divisores |
| `--color-ink` | `#000000` | Texto principal, botón primario |
| `--color-graphite` / `--color-smoke` / `--color-ash` | `#44403b` / `#777169` / `#a59f97` | Texto secundario / cuerpo / apoyo |
| `--color-violet-spark`, `--color-ember-orange` | `#0447ff`, `#ff4704` | Solo ilustración. **No se usan en la UI** |

No usar blanco puro de fondo: siempre eggshell.

## Tipografía

- **Waldenburg** (comercial) → sustituto **Inter 300** en titulares (48/36/32px, tracking −0.02em). Verificar licencia si se quiere la original.
- **Inter 400/500** para todo lo demás (14px base, tracking +0.01em); **Geist Mono** 12–13px solo para metadatos y fuentes. Fuentes locales vía `@fontsource-variable`, sin CDN (la app debe funcionar sin internet).

## Formas y componentes

- Tarjetas: taupe, radio 20px (escenario 24px), relleno 32px, sin borde ni sombra.
- Botones: píldora 9999px. **Primario** = negro relleno; **secundario** = contorno `#e5e5e5` sobre eggshell; **ghost** = sin contorno (navegación). Un solo primario por vista.
- Inputs y selects: radio 4px, borde `#e5e5e5`, flecha del select dibujada (sin apariencia nativa).
- Etiquetas de estado: píldora con punto de color **y texto**.
- Divisores: línea de 1px `--color-stone`.

## Movimiento (todo respeta `prefers-reduced-motion`)

| Animación | Para qué sirve |
|---|---|
| Anillo pulsante en la zona | Comunica estado: rojo rápido (1.3 s), amarillo lento (2.2 s), verde y sin datos quietos |
| Brillo bajo la zona seleccionada | Refleja el estado de la zona |
| Entrada del panel de detalle (280 ms) y de cada efecto (escalonado 50 ms) | Confirma el cambio de zona |
| Etiqueta flotante al pasar el cursor o enfocar | Nombra la zona |
| Flotación lenta del astronauta (7 s) | Alude a la microgravedad; decorativa |

Curva `cubic-bezier(0.16, 1, 0.3, 1)`; solo `transform` y `opacity`.

## Modo oscuro

`data-theme="dark"` en `<html>` redefine los tokens (`tokens.css`). Se elige por `prefers-color-scheme` la primera vez y se recuerda en `localStorage` (con `try/catch`); un script en `index.html` lo aplica antes de pintar para evitar parpadeo. El botón de sol/luna está en la barra; el cambio hace una transición de color de 0.4 s.

## Animaciones adicionales (`animaciones.css`)

Entrada escalonada de vistas y tarjetas · titular que se revela con desenfoque al cambiar de estado · contador de NEWS2 · elevación de tarjetas al pasar el cursor · puntos de estado que laten (rojo/amarillo) · filas que destellan cuando cambia su valor · esqueleto de carga · barrido de escaneo y onda al elegir zona · inclinación del astronauta con el cursor · indicador de canal que late en Enlace · icono de tema que gira. Con `prefers-reduced-motion` todo se reduce a cambios instantáneos.

## Adaptaciones para ORBIT (supuestos a confirmar)

1. **Semáforo clínico:** la guía es casi acromática y reserva violeta y naranja para ilustración. El estado clínico necesita verde/amarillo/rojo (`--estado-*`); es una excepción funcional y siempre va con texto.
2. **Waldenburg → Inter 300**, por licencia.
3. **Escala:** se usa 12px (no 10px) para captions, por legibilidad.
4. **Hero:** en lugar de la esfera de audio, el astronauta de la NASA con zonas interactivas ([FIGURA_HUMANA.md](./FIGURA_HUMANA.md)).
5. Revisar contraste del texto `--color-smoke` sobre taupe con una persona real antes de la demo.
