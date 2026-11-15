# ORBIT Health — Frontend Documentation

[Versión en español](./README.md)

Local clinical decision-support interface for deep-space crews operating under degraded communication links. Runs 100% offline and supports both **English (`EN`)** and **Spanish (`ES`)**.

---

## 1. Tech Stack & Principles

- **Framework:** React 18 + TypeScript 5
- **Bundler & Dev Server:** Vite 5 (`@vitejs/plugin-react`)
- **Testing:** Vitest + Testing Library (`@testing-library/react`, `jsdom`)
- **Styling:** Native CSS consolidated in [`src/shared/styles/styles.css`](../src/shared/styles/styles.css), supporting **light/dark** themes, adaptive performance tiers (`data-rendimiento`), frosted-ice top bar, transparent sidebar, and liquid-glass cards.
- **Internationalization (`i18n`):** Local dictionaries under `src/i18n/locales/{ES,EN}/` with live language switching from the top bar (`CambioIdioma`).
- **Golden Rule (100% Offline):**
  - Production builds (`frontend/dist/`) are served directly by FastAPI with zero internet dependency.
  - Fonts (`Inter`, `Geist Mono`), SVG icons, `.webp` assets, and the Service Worker (`public/sw.js`) are all bundled locally. External CDNs or non-`/api` requests are forbidden.

---

## 2. Development & Commands

From `frontend/`:

```bash
# Install dependencies
pnpm install   # or npm install

# Start dev server at http://localhost:3000
# Proxies /api/* -> http://localhost:8000 (see vite.config.ts)
npm run dev

# Type-check and build static bundle into frontend/dist/
npm run build

# Verify bundle size budget (JS, CSS, and images)
npm run perf

# Run all unit tests (31 files, 139 tests)
npx vitest run
```

> **Note:** When using `npm run dev`, start the FastAPI backend on port `8000` in another terminal:
> ```bash
> cd backend && uvicorn app.main:app --reload --port 8000
> ```

---

## 3. Directory Structure (`frontend/src/`)

Feature-oriented (*Screaming Architecture*) layout:

```text
frontend/src/
├── app/                          # App shell: App.tsx, BarraLateral, AsistenteFlotante, routes
├── features/
│   ├── asistente/                # Private chat with Nova (greeting, quick prompts, short memory, AI profile)
│   ├── banda/                    # Interactive 3D watch (RelojBanda), live simulated mission, and streak
│   ├── bienestar/                # Daily mood, private journal, PHQ-2 screening, crisis protocol & preferences
│   ├── bienvenida/               # Step-by-step onboarding guide for first-time crew members
│   ├── cabina/                   # Cabin environmental telemetry (CO₂ and radiation dose)
│   ├── enlace/                   # Earth/Moon/Mars link console, Eclipse Mode, SHA-256 queue, Earth & CSV reports
│   ├── historial/                # Filterable historical readings view
│   ├── mediciones/               # Manual vital signs entry panel
│   ├── monitor/                  # Primary clinical view: human body (.webp), NEWS2 ring, zones & vital signs
│   ├── peligros/                 # NASA HRP spaceflight hazards framework
│   ├── seguridad/                # AccesoTripulante (3D Earth login, PIN auth, recovery) & PerfilMenu
│   ├── sistema/                  # DB health, backups, commander PIN reset, shared alerts & audit verification
│   ├── tripulantes/              # Active crew member selector
│   └── voz/                      # Bilingual ES/EN voice bubble (local Whisper/Piper or Web Speech API)
├── i18n/                         # i18n engine and ES / EN locale files per feature
├── shared/                       # api/client.ts, UI components, hooks (useTema), performance & styles/styles.css
└── main.tsx                      # Initializes performance tier, theme, i18n, Service Worker & React root
```

---

## 4. Views & Key Capabilities

1. **Auth & Profile (`seguridad`)**: 3D Earth login screen (`Tierra3D`), PIN authentication, recovery flow, and logout from `PerfilMenu` in the top bar.
2. **Onboarding (`bienvenida`)**: Step-by-step walkthrough for first-time users.
3. **Monitor (`monitor` + `cabina` + `mediciones`)**: NEWS2 score ring, interactive human figure with realistic `.webp` layers (suit, skeleton, muscles, organs), vital sign cards, time-series charts, clinical actions, and manual entry.
4. **Band (`banda`)**: Interactive 3D smart band (`RelojBanda`), live simulated mission timeline, and measurement streak.
5. **History (`historial`)**: Historical readings per indicator and crew member.
6. **Wellbeing (`bienestar` + `voz`)**: Daily mood tracker, 100% local private journal, PHQ-2 screening, consent-based crisis protocol, and voice assistant.
7. **Assistant (`asistente`)**: Private text chat with **Nova** (contextual greeting, quick shortcuts, short-term memory, personal interests & traits profile), also available via the floating assistant button (`AsistenteFlotante`).
8. **Hazards (`peligros`)**: Overview of physiological and psychological spaceflight hazards.
9. **Link (`enlace`)**: Moon/Mars latency simulation, Eclipse Mode, priority queue with hash-chain integrity check, Earth-received messages view, and CSV report downloads.
10. **System (`sistema`)**: Server health and backups, commander PIN reset, shared mental-health alerts, and audit log verification.

---

## 5. Related Docs

- [Documentación en español](./README.md)
- [API reference](./API.md)
- [Architecture](./ARQUITECTURA.md)
- [Platform style guide](./ESTILO_PLATAFORMA.md)
- [Human figure](./FIGURA_HUMANA.md)
- [AI usage & frontend docs](./USO_IA_Y_DOCUMENTACION_FRONTEND.md)

---

## 6. AI Usage Justification & Transparency

In accordance with **NASA Space Apps Challenge** guidelines, AI tools were used strictly as **technical assistance** (component/hook implementation, CSS styling, unit tests, and documentation drafting) under the team's architecture, product decisions, and human verification. See full disclosure in [USO_IA_Y_DOCUMENTACION_FRONTEND.md](./USO_IA_Y_DOCUMENTACION_FRONTEND.md) and [docs/SI_DISCLOSURE.md](../../docs/SI_DISCLOSURE.md).
