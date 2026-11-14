# Sistema de diseño — referencia "Dala" adaptada a ORBIT Health

Tema oscuro, "constelación flotando sobre terciopelo negro": fondo negro puro, un solo acento violeta, chispas ámbar, tipografía ligera y mucho espacio. Fuente: guía de estilo compartida por el equipo.

Los tokens van en `shared/styles/tokens.css`.

## Colores

| Token | Valor | Uso |
|---|---|---|
| `--color-void` | `#000000` | Fondo de página y secciones |
| `--color-bone-white` | `#ffffff` | Titulares y texto principal |
| `--color-ash-gray` | `#9a9a9a` | Texto secundario, nav inactiva |
| `--color-silver-mist` | `#bdbdbd` | Texto terciario |
| `--color-electric-iris` | `#8052ff` | Botón primario y acentos de marca (nunca fondos grandes) |
| `--color-saffron-spark` | `#ffb829` | Etiquetas y énfasis |
| `--color-deep-verdant` | `#15846e` | Tinte secundario |

## Tipografía

- Familia: **PPNeueMontreal** → sustituto **Inter** (`--font-ppneuemontreal`). PPNeueMontreal parece ser fuente comercial: verificar licencia antes de usarla; mientras tanto, Inter.
- Titulares: peso 400, tracking negativo (≈ -0.04em desde 42px). Cuerpo 18px peso **200**. Nav/etiquetas: 14px peso 600, mayúsculas, 0.025em.
- Escala: 12 · 14 · 18 · 24 · 27 · 36 · 42 · 48 · 78 · 113 px (tokens `--text-*` en la guía original).

## Espaciado, radios, layout

- Unidad base 6px; escala 6/12/18/24/30/36/60/96/120.
- Radio 24px (botones, nav, tarjetas); `9999px` solo para etiquetas.
- Ancho máximo 1280px; separación entre secciones 60–120px.
- Sin sombras ni elevación; la jerarquía sale de escala, color y espacio.

## Componentes base

| Componente | Regla |
|---|---|
| Botón primario | Píldora `#8052ff`, texto blanco, 14px mayúsculas. **Uno solo por vista** |
| Enlace fantasma | Sin fondo ni borde, `#fff` / `#9a9a9a` |
| Navegación | Transparente sobre negro; logo a la izquierda, acción primaria a la derecha |
| Titular + cuerpo | Dos columnas asimétricas; titular grande a la izquierda |
| Partículas ambientales | Triángulos de 1–2px, solo decorativos |

## Reglas clave (de la guía)

- Fondo siempre `#000`; no usar paneles grises, tarjetas con borde ni sombras.
- Violeta solo en botones y acentos; sin degradados en componentes (solo logo y partículas).
- Cuerpo en peso 200, nunca 400.

## Adaptaciones para ORBIT (decisiones a confirmar)

1. **Imagen hero:** en lugar del cerebro de partículas, la **figura humana SVG** ([FIGURA_HUMANA.md](./FIGURA_HUMANA.md)), idealmente rodeada de partículas triangulares de baja opacidad. Es la excepción a "no hay otra imagen": aquí la figura es la interfaz.
2. **Semáforo clínico (verde / amarillo / rojo):** la guía no define colores de estado, pero el producto los necesita. **Supuesto:** usar tokens `--color-estado-verde`, `--color-estado-amarillo`, `--color-estado-rojo`, distintos de violeta y ámbar de marca para no confundir acento con alerta, y acompañarlos siempre de texto o icono (no depender solo del color).
3. **Densidad:** la guía es "una o dos cosas por pantalla". Un monitor clínico necesita más datos a la vez; **Supuesto:** mantener el espaciado y la tipografía de Dala, pero permitir listas de indicadores compactas bajo la figura.
4. **Sin tarjetas/bordes:** los paneles de captura y diario se separan con espacio, no con cajas.
5. **Accesibilidad:** el cuerpo en peso 200 sobre negro puede ser difícil de leer en emergencias; verificar contraste y legibilidad con una persona real antes de la demo.
6. **Aviso clínico** (prototipo, no sustituye criterio médico) siempre visible, en `--color-saffron-spark`.
