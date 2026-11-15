# Super Intelligence (SI) tools: disclosure

The NASA Space Apps Challenge requires every project to state where and how SI tools were used, and says SI must not be used to come up with the idea of how to solve the challenge. This file answers that for the repository. Items marked **[TEAM TO CONFIRM]** can only be answered by the people who did that work.

## Tools used
- **Claude (Anthropic), through Claude Code**, working directly in this repository during the hackathon.

## What SI tools did in this repository
| Area | Use of SI | How it is marked |
|---|---|---|
| Backend code (`backend/app/`) | Wrote the implementation: API, services, repositories, clinical rules engine, outbound queue, authentication, self-recovery | Commit trailer `Co-Authored-By: Claude` (74 of 100 commits when this was updated: all 65 by the backend author and 9 of 12 by one frontend developer; the other team members' commits carry no trailer, which does not by itself show whether they used other AI tools) |
| Tests (`backend/tests/`) | Wrote and ran the automated tests | Same trailer |
| Scripts (`scripts/`, `run.sh`) | Wrote start-up, end-to-end check, backup and calibration scripts | Same trailer |
| Documentation (`README.md`, `README.es.md`, `docs/`) | Drafted technical documentation, decision records and the English summary | Same trailer |
| Research | Read the official challenge pages and public references while building | Cited in `docs/PROJECT_SUMMARY_EN.md` |

## SI inside the product (optional)
The product can use a **local language model** (no internet) to rephrase an alert and to answer by voice. It never sets the alert level, crisis messages are always the written protocol and never go through the model, and every model output is checked (no invented numbers, medication, links or foreign alert levels) and labelled as AI-generated. Details: `docs/IA_LOCAL.md`. An optional external provider (DeepSeek, over the internet) can be enabled with an API key; when it is, the user's question and calculated health state leave the device, the response says so, and it is meant for development and demos, not for the offline mission scenario. No model is bundled and none has been clinically validated.

## What SI tools did not do
- The backend author did not generate images, video or audio with SI. The frontend artwork is a separate matter: the origin and licence of the astronaut illustration are still being confirmed (see `frontend/src/features/monitor/assets/ATRIBUCION.md`), and any SI-generated image must carry a visible watermark.
- No NASA branding was used or modified.
- Clinical thresholds were **not** validated by SI or by anyone yet. They are design assumptions and the interface says so on screen.

## The idea
- **[TEAM TO CONFIRM]** Who defined the concept (decision support that works offline, deterministic and explainable rules, privacy of mental-health data) and who chose the indicators and the overall approach. State here, in the team's own words, what the team decided before and independently of any SI suggestion.
- **[TEAM TO CONFIRM]** Which SI tools, if any, were used for the commits without a trailer (parts of the frontend, the delivery logic and the psychological-crisis protocol), and whether any were used for the demo script or the slides.
- **[TEAM TO CONFIRM]** Where the astronaut illustration (`astronauta.svg`) came from, whether it was generated with SI, and under what licence it may be published.

## Data
- Calibration series come from the BIDMC PPG and Respiration Dataset (PhysioNet, Open Data Commons Attribution License v1.0). Attribution is in `data/physionet/ATRIBUCION.md`.
