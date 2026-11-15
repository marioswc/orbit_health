# 03 — Clinical Assistant & Local AI / Voice

## What problem existed
During a space mission an astronaut may have their hands full or want a plain-language summary of their status without internet access—yet an AI must never invent diagnoses or change clinical alert levels.

## How it was solved
- **Dedicated Assistant tab ([AsistentePage.tsx](../../src/features/asistente/routes/AsistentePage.tsx), [ExplicacionEstado.tsx](../../src/features/asistente/components/ExplicacionEstado.tsx), commit `feef45a`):**
  - Moved communication preferences (*direct or warm tone, detail level, reminder frequency*) from Wellbeing into this dedicated tab.
  - Connected the plain-language status explanation (`GET /api/estado/{tid}/explicacion`): if an onboard local model is running, it summarizes the already-computed status with an AI-generated notice; otherwise it immediately falls back to deterministic local rules.
- **Floating push-to-talk voice bubble ([BurbujaVoz.tsx](../../src/features/voz/components/BurbujaVoz.tsx), commits `feef45a`, `507c8aa`, `2eb001e`):**
  - Integrated a floating voice bubble (`POST /api/voz/chat/{tid}`) with clear turn states (*Ready, Listening, Processing, Speaking*) and AI disclosure tags.
  - Fixed React `StrictMode` double-mount edge cases so the bubble never gets stuck in *"Processing"*, and removed a duplicate floating button in `App.tsx`.
- **Transparent operational note:**
  - Server-side speech-to-text and voice synthesis activate only when local voice models and environment flags (`ORBIT_VOZ_ACTIVA=1`) are configured; when disabled, the UI clearly reports that local voice is off without disrupting the rest of the app.


---

> **AI Signature & Justification (SI Disclosure):**
> - **Tool used:** **Claude (Anthropic)** via **Claude Code**.
> - **Justification:** Used as a technical assistant during the hackathon to draft and structure the frontend documentation, UI architecture, and component guides, under the human team's visual design, UX decisions, and validation (in compliance with *NASA Space Apps Challenge* rules).
