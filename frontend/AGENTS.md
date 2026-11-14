# Reglas del frontend — ORBIT Health

## Estilo
- El estilo vigente es el de `docs/ESTILO_PLATAFORMA.md`. Es la fuente de verdad visual; el código está en `src/shared/styles/` (`tokens.css`, `styles.css`, `componentes.css`, `escenario.css`, `animaciones.css`).
- No usar `docs/DISENO.md` (referencia Dala, descartada) ni el CSS de la primera versión.
- Colores, espaciado, radios y tipografía salen de los tokens (`--color-*`, `--estado-*`, `--hud`, `--spacing-*`). No poner valores sueltos.
- Todo componente nuevo debe verse bien en modo claro y oscuro (`data-theme`).
- Tipografía: Inter para texto, Geist Mono para etiquetas y datos. Todo local, sin CDN.

## Reglas de diseño
- El color se reserva para el semáforo clínico y el azul HUD. El estado nunca va solo con color: siempre con texto.
- Paneles con liquid glass (`.cristal`, `.panel`). Máximo 4 superficies con `backdrop-filter` a la vez; no aplicarlo al escenario del astronauta.
- Animar solo `transform` y `opacity`; respetar `prefers-reduced-motion`.
- Accesibilidad: objetivos de 40 px o más, foco visible, `aria-label` con el estado.

## Estructura
- Organización por features: `src/features/<nombre>/` y `src/shared/`. Ver `docs/ARQUITECTURA.md`.

## Offline
- Sin fuentes, iconos ni scripts remotos. El build debe funcionar sin internet.

## Cuando falte algo
- Si el estilo no cubre un caso, proponer la adición en `ESTILO_PLATAFORMA.md` marcándola como **Supuesto**; no inventar un estilo aparte.

