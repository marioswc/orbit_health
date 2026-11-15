# ORBIT Health

Offline health decision support for astronauts on long missions, where messages to Earth are delayed or interrupted and nobody can evacuate the crew. Built for the NASA Space Apps Challenge 2026: *Create Health Monitoring Software for Astronauts on Space Missions*.

A Spanish version for the team is kept in `README.es.md` (internal, not part of the submission). The material for judges is here:

| Document | What it is |
|---|---|
| [docs/PROJECT_SUMMARY_EN.md](docs/PROJECT_SUMMARY_EN.md) | What the project does, the sources used and the honest limitations |
| [docs/SI_DISCLOSURE.md](docs/SI_DISCLOSURE.md) | How Super Intelligence (AI) tools were used, as the challenge requires |
| [docs/DEMO_SCRIPT_EN.md](docs/DEMO_SCRIPT_EN.md) | Script for the 30-second video and the 7-slide deck |
| [docs/PERFORMANCE_EN.md](docs/PERFORMANCE_EN.md) | Measured response times, with their limits |

## What it does
- Scores vital signs on board with the published NEWS2 scheme plus rules that combine signals, and tells the crew what to do now (repeat, notify, measure again). It never suggests treatment.
- Keeps a personal rolling baseline for each crew member and explains each measurement in plain words, with links to the official sources.
- Queues events during a blackout and sends the most urgent first when the link returns, with a simulated delay, a round-trip confirmation and a tamper-evident hash chain.
- Links every alert to NASA's Human Research Program hazards and shows, risk by risk, what it covers. Honest count: 1 of 17 risks fully, 7 partly, 9 not covered.
- Keeps the diary, the PHQ-2 screening and the daily mood score private to their owner; none is ever queued for Earth. Only a notice the crew member explicitly chooses to send (revocable, audited, without the diary or the score) can reach the flight surgeon or the commander.
- Adapts its wording to each astronaut's chosen tone and level of detail, without changing any alert level.
- Verifies and restores its own database and exports a report for Earth with an integrity fingerprint.

## One-file executable (no Python or Node needed)
`scripts/crear_ejecutable.sh` builds a single ~24 MB file for your OS that starts the server and opens its own app window (Chromium app mode, no tabs or address bar; closing the window stops the server; falls back to the normal browser) with a double-click. Data is kept in the user's own folder and it only listens on 127.0.0.1. It is unsigned, so Windows and macOS show a security warning the first time. Details and limits: `docs/EJECUTABLE.md` (in Spanish).

## Install it as an app / run it in a container
ORBIT Health is an installable web app (PWA): open it in Chrome or Edge and use the *Install* prompt. It opens in its own window and the interface loads even if the server is slow. Clinical data is never cached in the browser. Installing needs `localhost` or HTTPS. Or run it in Docker: `docker compose up --build` (http://127.0.0.1:3000, loopback only). Details and limits: `docs/INSTALAR_COMO_APP.md` (in Spanish).

## Run it (works without internet once prepared)
Requirements: Python 3.10+ and Node.js with npm. Optional offline AI and voice: `scripts/instalar_ia_local.sh` and `scripts/instalar_voz_local.sh` (see `docs/IA_LOCAL.md`, in Spanish).

```bash
scripts/asistente_inicio.sh --en # friendly step-by-step setup that asks you questions (recommended if you are new)
scripts/preparar.sh          # or, non-interactive, one step on a new machine: Python env, dependencies, build, .env (needs internet once)
./run.sh                     # http://127.0.0.1:3000, no network needed
scripts/cuentas_demo.sh      # optional: demo PIN accounts (set ORBIT_AUTH=1 in .env): T1 111111, T2 222222, T3 333333, T4 444444
scripts/verificar_e2e.sh     # automatic end-to-end check
curl -X POST "localhost:3000/api/demo/escenarios/hipoxia_eclipse?reconectar=true"   # scripted demo
```

## Honest limitations
- A prototype that supports decisions; it does not replace the flight surgeon.
- **All clinical thresholds are design assumptions pending validation by a clinician.** The interface says so.
- Vital signs are entered by hand, through a simulated device or, for heart rate only, through a Bluetooth bridge (details in `docs/BANDA_BLE.md`, internal and in Spanish) that is tested with simulated packets. A real consumer band (IDW26, Veryfit app) connected but uses a proprietary protocol, so it is **not supported**.
- No encryption at rest and no TLS on the cabin network yet; local PIN authentication exists but is off by default.
- The calibration data are records of critically ill hospital patients (BIDMC dataset, PhysioNet), not of astronauts.


---

> **AI Signature & Justification (SI Disclosure):**
> - **Tool used:** **Claude (Anthropic)** via **Claude Code**.
> - **Justification:** Used as a technical assistant during the hackathon to draft and structure technical documentation, record architectural decisions, and maintain traceability with the source code and public NASA references, under the human team's conceptual definition, review, and validation (in compliance with *NASA Space Apps Challenge* rules).
