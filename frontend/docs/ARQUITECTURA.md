# Arquitectura del frontend — Screaming Architecture

La estructura de carpetas **grita el dominio** (monitoreo de salud de astronautas), no el framework. Se organiza por **features** autocontenidas y módulos transversales en `shared/` e `i18n/`.

## Estructura actual (`frontend/src/`)

```text
frontend/src/
├── app/                          # Composición: App.tsx, BarraLateral.tsx, AsistenteFlotante.tsx, rutas.ts
├── features/
│   ├── asistente/                # Chat privado con Nova (saludo, atajos, perfil IA, memoria corta)
│   ├── banda/                    # Reloj 3D (RelojBanda), simulación de misión y racha de mediciones
│   ├── bienestar/                # Ánimo diario, diario privado, tamizaje PHQ-2, protocolo de crisis
│   ├── bienvenida/               # Guía inicial paso a paso
│   ├── cabina/                   # Monitor ambiental de cabina (CO₂ y dosis de radiación)
│   ├── enlace/                   # Consola de enlace, Modo Eclipse, cola SHA-256, Tierra e informes
│   ├── historial/                # Registro histórico de lecturas por indicador
│   ├── mediciones/               # Captura manual de signos vitales
│   ├── monitor/                  # Figura humana (.webp), NEWS2, signos vitales, acciones y series
│   ├── peligros/                 # Marco de riesgos NASA HRP
│   ├── seguridad/                # AccesoTripulante (Tierra 3D, login PIN, recuperación) y PerfilMenu
│   ├── sistema/                  # Salud, respaldos, reinicio de PIN, avisos compartidos y auditoría
│   ├── tripulantes/              # Selector de tripulante activo
│   └── voz/                      # Burbuja de voz bilingüe ES/EN (Whisper/Piper local o Web Speech API)
├── i18n/                         # Motor i18n y locales ES / EN por feature
├── shared/                       # api/client.ts, components/, hooks/, styles/styles.css, types/, rendimiento.ts
└── main.tsx
```

## Reglas

1. **Una feature no importa de otra feature.** Si dos la necesitan, sube a `shared/` o se coordina desde `app/`.
2. Cada feature expone su API pública por `index.ts`.
3. `components/` = UI. `hooks/` = estado y efectos. `types/` = contratos. `routes/` = vistas cargadas en `app/App.tsx` con `React.lazy`.
4. `shared/` no importa de `features/`. `app/` puede importar de ambos.
5. Toda llamada a `/api` pasa por `shared/api/client.ts` (o `fetch` directo a `/api/voz/chat/{id}` para multipart de audio). Sin URLs externas ni secretos en cliente.
6. Los umbrales clínicos viven en el backend. El frontend **no recalcula niveles**: solo muestra los que devuelve la API.

## Navegación y carga diferida

- `app/rutas.ts` define la navegación por hash (`#/monitor`, `#/banda`, `#/historial`, `#/bienestar`, `#/asistente`, `#/riesgos`, `#/enlace`, `#/sistema`), y `app/App.tsx` carga las páginas de forma diferida (`React.lazy` + `Suspense`) para mantener bajo el bundle inicial.
- En pantallas de acceso (`AccesoTripulante`) se muestra el escenario `Tierra3D` y los controles de idioma/tema hasta completar el login (o usar modo sin autenticación cuando `ORBIT_AUTH=0`).

## Feature → riesgo NASA HRP / necesidad operativa

| Feature | Riesgo o necesidad que atiende |
|---|---|
| `monitor`, `mediciones`, `historial` | Cardiovascular, hipoxia, inmune, pérdida ósea y seguimiento longitudinal |
| `cabina`, `banda` | Ambiente de cabina (CO₂, radiación) y telemetría continua de pulsera |
| `bienestar`, `asistente`, `voz` | Salud conductual, aislamiento, confinamiento y apoyo privado con Nova |
| `enlace` | Distancia a la Tierra: retardo, Modo Eclipse y cola priorizada SHA-256 |
| `seguridad`, `sistema` | Privacidad a bordo (PIN, permisos por rol), respaldos y auditoría íntegra |

---

## Justificación del uso de IA

La arquitectura orientada a dominio (*Screaming Architecture*), la separación entre features y la regla de no recalcular umbrales en cliente fueron definidas por el equipo; la IA apoyó en la refactorización, tipado y pruebas unitarias bajo revisión humana. Ver [USO_IA_Y_DOCUMENTACION_FRONTEND.md](./USO_IA_Y_DOCUMENTACION_FRONTEND.md) y [docs/SI_DISCLOSURE.md](../../docs/SI_DISCLOSURE.md).


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación de frontend, arquitectura de interfaz y componentes, bajo el diseño visual, criterio de experiencia de usuario y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
