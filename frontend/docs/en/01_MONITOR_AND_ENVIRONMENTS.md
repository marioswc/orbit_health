# 01 — Monitor & Mission Environments

## What problem existed
A traditional medical dashboard shows dozens of raw numbers that are hard to scan quickly during an emergency, and it does not distinguish where the astronaut is in the mission (for example, the 1–1.5 % monthly bone density loss estimate applies to microgravity, not to the Moon or Mars).

## How it was solved
- **Unified mission dashboard ([MonitorPage.tsx](../../src/features/monitor/routes/MonitorPage.tsx), commit `8e99522`):**
  - Organized the screen into three clear areas: key metrics on the left (**NEWS2** clinical score ring, heart pulse, cabin environment, and trend chart); selected zone details, vital signs list, and suggested actions in the center; and the **interactive astronaut** on the right.
  - Clicking any body zone (head, respiratory, cardiovascular, torso, arms, or legs) or switching anatomy layers (*Suit, Muscle, Bone, Organs*) zooms into that area and filters to its relevant readings.
- **Gravity-aware environments ([useEntornos.ts](../../src/features/monitor/hooks/useEntornos.ts), [DetalleZona.tsx](../../src/features/monitor/components/DetalleZona.tsx), commit `73c01c4`):**
  - Added an environment selector powered by the backend (`GET /api/entornos`).
  - The bone density loss slider/calculation is shown **only** when the selected environment has microgravity; on the Moon, Mars, or rover, the calculation is hidden and replaced by an accurate explanatory note.
- **NASA-cited explanations ([ExplicacionIndicador.tsx](../../src/features/monitor/components/ExplicacionIndicador.tsx), commit `73c01c4`):**
  - Each indicator displays what signs to watch for and countermeasures with verbatim quotes and links to official NASA sources—or explicitly states when the source provides no guidance.
- **Gentle reminders & streak ([RecordatorioCaptura.tsx](../../src/features/monitor/components/RecordatorioCaptura.tsx), [RachaMediciones.tsx](../../src/features/monitor/components/RachaMediciones.tsx), commits `9f6e98e`, `73c01c4`):**
  - Shows when the next check is due based on the crew member's status and tracks consecutive monitoring days without punitive alerts while today is still in progress.
- **Faster startup rendering (commit `3ab9737`):**
  - Reduced duplicate requests on startup and eliminated unnecessary layout recalculations in the Monitor view.


---

> **AI Signature & Justification (SI Disclosure):**
> - **Tool used:** **Claude (Anthropic)** via **Claude Code**.
> - **Justification:** Used as a technical assistant during the hackathon to draft and structure the frontend documentation, UI architecture, and component guides, under the human team's visual design, UX decisions, and validation (in compliance with *NASA Space Apps Challenge* rules).
