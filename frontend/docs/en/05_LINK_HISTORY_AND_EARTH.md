# 05 — Link, History & Earth View

## What problem existed
On Moon or Mars missions, signals are delayed or cut off completely during blackouts. The crew needs to see which messages are queued, run live failure-tolerance demos, download Earth reports, and inspect full measurement history without cluttering the screen.

## How it was solved
- **Link Console & blackout tolerance ([EnlacePage.tsx](../../src/features/enlace/routes/EnlacePage.tsx), [ConsolaEnlace.tsx](../../src/features/enlace/components/ConsolaEnlace.tsx), commits `905657a`, `b2b942c`):**
  - Displays live link status (active vs. blackout), environment-based latency (Orbit, Moon, Mars), and counts of **held**, **in-transit**, and **received** messages.
  - Includes queue integrity verification (`/api/cola/verificar`) to prove no records were altered during a blackout.
- **Live mission simulator ([SimuladorDemo.tsx](../../src/features/enlace/components/SimuladorDemo.tsx), commits `73c01c4`, `f8a3cec`):**
  - Connected controls to **start and stop the live simulated mission**, load preset scenarios, and compare latency across environments.
- **Earth View & report downloads ([VistaTierra.tsx](../../src/features/enlace/components/VistaTierra.tsx), commit `9f6e98e`):**
  - Lists clinical messages delivered to Earth and provides direct download links for the crew report.
- **Collapsible, paginated History table ([HistorialPage.tsx](../../src/features/historial/routes/HistorialPage.tsx), commits `25b68ba`, `8e99522`, `8573833`):**
  - Replaced long hard-to-scan lists with a structured table featuring expandable rows, per-indicator charts, and pagination.


---

> **AI Signature & Justification (SI Disclosure):**
> - **Tool used:** **Claude (Anthropic)** via **Claude Code**.
> - **Justification:** Used as a technical assistant during the hackathon to draft and structure the frontend documentation, UI architecture, and component guides, under the human team's visual design, UX decisions, and validation (in compliance with *NASA Space Apps Challenge* rules).
