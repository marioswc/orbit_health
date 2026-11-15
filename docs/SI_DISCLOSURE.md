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
- The backend author did not generate images or video with SI. Two disclosures: the app icons are drawn programmatically by a script written with Claude Code (`scripts/generar_iconos.py`, no image-generation model), and when the optional voice is on, Nova's spoken replies are synthesised at runtime by a neural text-to-speech model (Piper) and speech is recognised by a neural model (faster-whisper); no pre-generated audio is stored in the repository. The frontend artwork is a separate matter: the origin and licence of the astronaut illustration are still being confirmed (see `frontend/src/features/monitor/assets/ATRIBUCION.md`), and any SI-generated image must carry a visible watermark.
- No NASA branding was used or modified.
- Clinical thresholds were **not** validated by SI or by anyone yet. They are design assumptions and the interface says so on screen.

## The idea
- **Concept (team statement).** The concept and the approach come from the team's own analysis of the challenge statement and the resources linked to it (NASA Human Research Program hazard and risk pages, the ARCHeR study description and related public documents). That analysis defined the problem: offline decision support for a crew without a doctor, deterministic and explainable rules, and privacy of mental-health data. SI tools were used afterwards to help implement and document that approach; SI was not used to come up with the idea of how to solve the challenge.
- **SI tools by contributor, from the Git history** (at the time of writing): **Claude (Anthropic), through Claude Code**, appears as co-author in 146 commits by the backend author and 21 commits by Santiago Antonio Suárez Luna; **GitHub Copilot** appears as co-author in 2 commits by vzdee; **Antigravity (Google DeepMind)** was used by Mauricio Martinez for the presentation structure and executive summary, as stated in his documents. Commits by Lourdes Ruiz and the remaining commits by vzdee and Mauricio carry no trailer. **[TEAM TO CONFIRM: each of those three members, whether any SI tool was used in the commits without a trailer, and whether any was used for the demo script or slides.]**
- **Images (team statement):** no image or video in the project was generated with SI. The **origin and licence** of the astronaut illustration (`astronauta.svg`) and the skeleton and muscle layers are still to be confirmed (see the `ATRIBUCION.md` files); until they are, they should not be published or must be replaced.

## Data
- Calibration series come from the BIDMC PPG and Respiration Dataset (PhysioNet, Open Data Commons Attribution License v1.0). Attribution is in `data/physionet/ATRIBUCION.md`.


---

> **AI Signature & Justification (SI Disclosure):**
> - **Tool used:** **Claude (Anthropic)** via **Claude Code**.
> - **Justification:** Used as a technical assistant during the hackathon to draft and structure technical documentation, record architectural decisions, and maintain traceability with the source code and public NASA references, under the human team's conceptual definition, review, and validation (in compliance with *NASA Space Apps Challenge* rules).
