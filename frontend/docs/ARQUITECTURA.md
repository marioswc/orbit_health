# Arquitectura del frontend — Screaming Architecture

La estructura de carpetas debe **gritar el dominio** (monitoreo de salud de astronautas), no el framework. Se organiza por **features**; cada feature es autocontenida.

## Estructura objetivo

```text
frontend/src/
├── app/                          # Composición de la aplicación
│   ├── App.tsx                   # Layout raíz
│   ├── routes.tsx                # Tabla de rutas/vistas (une las rutas de cada feature)
│   └── providers/                # Contextos globales (tripulante activo, etc.)
├── features/
│   ├── monitor/                  # Vista principal: figura humana + resumen
│   │   ├── components/           # FiguraHumana, ResumenNews2, TarjetaZona
│   │   ├── hooks/                # useEstadoTripulante, useZonaSeleccionada
│   │   ├── routes/               # MonitorPage.tsx
│   │   ├── services/             # llamadas a /estado
│   │   ├── types/                # Estado, LecturaEstado, Nivel
│   │   └── index.ts              # API pública del feature
│   ├── mediciones/               # Captura manual de signos vitales
│   │   ├── components/           # PanelMedicion
│   │   ├── hooks/                # useRegistrarLectura
│   │   ├── services/             # POST /lecturas
│   │   └── types/
│   ├── bienestar/                # Tamizaje PHQ-2 + diario privado
│   │   ├── components/           # Tamizaje, DiarioTripulante
│   │   ├── hooks/
│   │   ├── routes/               # BienestarPage.tsx
│   │   ├── services/             # /tamizajes, /diario
│   │   └── types/
│   ├── enlace/                   # Enlace con la Tierra, modo Eclipse, cola
│   │   ├── components/           # ConsolaEnlace, ColaPrioridad
│   │   ├── hooks/                # useEnlace, useCola
│   │   ├── routes/               # EnlacePage.tsx
│   │   ├── services/             # /enlace, /cola, /cola/verificar
│   │   └── types/
│   └── tripulantes/              # Selector de tripulante
│       ├── components/ · hooks/ · services/ · types/
├── shared/                       # Solo lo que usan 2+ features
│   ├── api/                      # client.ts (fetch base)
│   ├── components/               # Boton, Etiqueta, Aviso, BadgeNivel
│   ├── hooks/
│   ├── styles/                   # tokens.css, globals.css
│   └── types/                    # Nivel y tipos transversales
└── main.tsx
```

## Reglas

1. **Una feature no importa de otra feature.** Si dos la necesitan, sube a `shared/` o se coordina desde `app/`.
2. Cada feature expone su API pública solo por `index.ts`. Nadie importa rutas internas de otra feature.
3. `components/` = UI sin lógica de red. `hooks/` = estado y efectos. `services/` = llamadas HTTP. `types/` = contratos.
4. `shared/` no importa de `features/`. `app/` puede importar de ambos.
5. Las llamadas a `/api` pasan siempre por `shared/api/client.ts`. Sin URLs ni secretos en componentes (usar variables de entorno de Vite, `import.meta.env`).
6. Los umbrales clínicos viven en el backend. El frontend **no recalcula niveles**: solo muestra los que devuelve la API.

## Mapa de migración (hecho el 2026-11-14)

| Hoy | Destino |
|---|---|
| `src/App.tsx` | `app/App.tsx` (+ vistas en `features/*/routes`) |
| `src/components/FiguraHumana.tsx` | `features/monitor/components/FiguraHumana.tsx` |
| `src/components/PanelMedicion.tsx` | `features/mediciones/components/` |
| `src/components/Tamizaje.tsx` | `features/bienestar/components/` |
| `src/components/DiarioTripulante.tsx` | `features/bienestar/components/` |
| `src/components/ConsolaEnlace.tsx` | `features/enlace/components/` |
| `src/api/client.ts` | `shared/api/client.ts` |
| `src/api/tipos.ts` | Repartir por feature; `Nivel` a `shared/types/` |
| `src/styles.css` | `shared/styles/` (tokens + globals), ver [DISENO.md](./DISENO.md) |

Migración aplicada solo de ubicación, sin cambiar comportamiento; `pnpm build` en verde. Diferencias frente a la estructura objetivo:

- Aún no existen `app/routes.tsx`, `app/providers/` ni `features/*/services/`; las carpetas vacías (`services/`, `hooks/`, `shared/components`, `shared/hooks`) se crearán al usarlas.
- Las llamadas HTTP siguen dentro de los componentes vía `shared/api/client.ts`; moverlas a `services/` es el siguiente paso.
- `MonitorPage` recibe `children` para que `app/` componga `PanelMedicion` (feature `mediciones`) sin que `monitor` importe de otra feature.
- `src/styles.css` pasó a `shared/styles/styles.css`; los tokens de [DISENO.md](./DISENO.md) aún no están aplicados.

## Navegación

Hoy `App.tsx` alterna vistas con estado local (`monitor` / `bienestar` / `enlace`). Decisión pendiente (**Supuesto**: se mantiene así para el prototipo, ya que el plan pide pantalla única sin rutas anidadas). Si se adopta un router, cada feature declara sus rutas en `routes/` y `app/routes.tsx` las une.

## Feature → riesgo HRP que atiende

| Feature | Riesgos/peligros NASA HRP |
|---|---|
| `monitor` | Cardiovascular, hipoxia, inmune, nutrición (indicadores en la figura) |
| `mediciones` | Captura manual cuando no hay sensores |
| `bienestar` | Salud conductual, aislamiento y confinamiento |
| `enlace` | Distancia de la Tierra: retardo, modo Eclipse, cola con prioridad |
