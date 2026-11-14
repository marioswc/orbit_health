# Super Intelligence (SI) tools: disclosure

The NASA Space Apps Challenge requires every project to state where and how SI tools were used, and says SI must not be used to come up with the idea of how to solve the challenge. This file answers that for the repository. Items marked **[TEAM TO CONFIRM]** can only be answered by the people who did that work.

## Tools used
- **Claude (Anthropic), through Claude Code**, working directly in this repository during the hackathon.

## What SI tools did in this repository
| Area | Use of SI | How it is marked |
|---|---|---|
| Backend code (`backend/app/`) | Wrote the implementation: API, services, repositories, clinical rules engine, outbound queue, authentication, self-recovery | Commit trailer `Co-Authored-By: Claude` (51 of 59 commits when this file was written) |
| Tests (`backend/tests/`) | Wrote and ran the automated tests | Same trailer |
| Scripts (`scripts/`, `run.sh`) | Wrote start-up, end-to-end check, backup and calibration scripts | Same trailer |
| Documentation (`README.md`, `docs/`) | Drafted technical documentation, decision records and the English summary | Same trailer |
| Research | Read the official challenge pages and public references while building | Cited in `docs/PROJECT_SUMMARY_EN.md` |

## What SI tools did not do
- No images, video or audio were generated with SI.
- No NASA branding was used or modified.
- Clinical thresholds were **not** validated by SI or by anyone yet. They are design assumptions and the interface says so on screen.

## The idea
- **[TEAM TO CONFIRM]** Who defined the concept (decision support that works offline, deterministic and explainable rules, privacy of mental-health data) and who chose the indicators and the overall approach. State here, in the team's own words, what the team decided before and independently of any SI suggestion.
- **[TEAM TO CONFIRM]** Whether SI tools were also used for the frontend, the demo script or the slides.

## Data
- Calibration series come from the BIDMC PPG and Respiration Dataset (PhysioNet, Open Data Commons Attribution License v1.0). Attribution is in `data/physionet/ATRIBUCION.md`.
