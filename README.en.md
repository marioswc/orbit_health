# ORBIT Health

Offline health decision support for astronauts on long missions, where messages to Earth are delayed or interrupted and nobody can evacuate the crew. Built for the NASA Space Apps Challenge 2026: *Create Health Monitoring Software for Astronauts on Space Missions*.

Spanish documentation is in [README.md](README.md). The material for judges is here:

| Document | What it is |
|---|---|
| [docs/PROJECT_SUMMARY_EN.md](docs/PROJECT_SUMMARY_EN.md) | What the project does, the sources used and the honest limitations |
| [docs/SI_DISCLOSURE.md](docs/SI_DISCLOSURE.md) | How Super Intelligence (AI) tools were used, as the challenge requires |
| [docs/PERFORMANCE_EN.md](docs/PERFORMANCE_EN.md) | Measured response times, with their limits |

## What it does
- Scores vital signs on board with the published NEWS2 scheme plus rules that combine signals, and tells the crew what to do now (repeat, notify, measure again). It never suggests treatment.
- Keeps a personal rolling baseline for each crew member and explains each measurement in plain words, with links to the official sources.
- Queues events during a blackout and sends the most urgent first when the link returns, with a simulated delay, a round-trip confirmation and a tamper-evident hash chain.
- Links every alert to NASA's Human Research Program hazards and shows, risk by risk, what it covers. Honest count: 1 of 17 risks fully, 6 partly, 10 not covered.
- Keeps the diary, the PHQ-2 screening and the daily mood score private to their owner; they are never queued for Earth.
- Adapts its wording to each astronaut's chosen tone and level of detail, without changing any alert level.
- Verifies and restores its own database and exports a report for Earth with an integrity fingerprint.

## Run it (works without internet once prepared)
```bash
cp .env.example .env
cd frontend && npm install && npm run build && cd ..          # needs internet once
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ..   # needs internet once
./run.sh                                                      # http://localhost:3000, no network needed
scripts/verificar_e2e.sh                                      # automatic end-to-end check
curl -X POST "localhost:3000/api/demo/escenarios/hipoxia_eclipse?reconectar=true"   # scripted demo
```

## Honest limitations
- A prototype that supports decisions; it does not replace the flight surgeon.
- **All clinical thresholds are design assumptions pending validation by a clinician.** The interface says so.
- Vital signs are entered by hand; there is no sensor integration yet.
- No encryption at rest and no TLS on the cabin network yet; local PIN authentication exists but is off by default.
- The calibration data are records of critically ill hospital patients (BIDMC dataset, PhysioNet), not of astronauts.
