# 02 — Wristband & Live Simulation

## What problem existed
Initially the interface relied on a prominent **"Manual capture"** floating button to enter vitals by hand, which does not reflect how a crew uses a wearable biometric band (such as an actigraphy/heart-rate wrist device). Also, during demos it needed to be unmistakably clear when data came from a real sensor versus a simulation.

## How it was solved
- **Dedicated Band view with interactive 3D watch ([BandaPage.tsx](../../src/features/banda/routes/BandaPage.tsx), [RelojBanda.tsx](../../src/features/banda/components/RelojBanda.tsx), commits `c413dee`, `8573833`, `64c209f`, `feef45a`):**
  - Added a dedicated tab rendering the astronaut's wrist device with 3D rotation, full strap, and touch/swipe gestures to switch watch screens with a finger.
  - Displays live crew readings and the measurement streak directly on the wearable view.
- **Removal of Manual Capture from the main UI ([App.tsx](../../src/app/App.tsx), commit `4e32de8`):**
  - Removed the floating `+ Manual capture` button and its side drawer so the workflow centers on automatic readings from the wearable (via Bluetooth bridge) or live mission simulation.
- **Honest `simulado` origin labeling ([SimuladorDemo.tsx](../../src/features/enlace/components/SimuladorDemo.tsx), commit `a0e80ab`):**
  - Updated simulator labels so demonstration readings are explicitly identified as **simulated** rather than physical sensor readings.


---

> **AI Signature & Justification (SI Disclosure):**
> - **Tool used:** **Claude (Anthropic)** via **Claude Code**.
> - **Justification:** Used as a technical assistant during the hackathon to draft and structure the frontend documentation, UI architecture, and component guides, under the human team's visual design, UX decisions, and validation (in compliance with *NASA Space Apps Challenge* rules).
