# Project page: text ready to paste (NASA Space Apps Challenge 2026, "Health Monitoring Software")

Everything below is in English because the official guide requires English on the submission page and in any linked material. Text in **[BRACKETS]** is a fact only the team can supply; do not submit with brackets left in.

## Before you press "Submit for Judging" (not part of the form)
1. **The repository is currently PRIVATE** (`marioswc/orbit_health`). The guide requires a *publicly accessible link, with no login*. Judges cannot evaluate a private repository. The owner must decide how to share: make the repository public, or share a public release or a public file link. Test the link in a private browser window.
2. **Do not make it public until the image licences are settled.** `astronauta.svg` and `esqueleto.webp` are marked "pending confirmation" in `frontend/src/**/ATRIBUCION.md` (the originals carried a watermark). Replace them or confirm the licence first.
3. The repository has **no LICENSE file**. Choose one (the team's decision) before publishing.
4. Deadline: **Sunday 15 November, 11:59 pm local time of your Local Event**. Every field must be in English, and nobody under 18 may appear in the demo.
5. Demo: a video of 30 seconds or less **with English subtitles**, or a deck of at most 7 slides in English (a 5-slide structure is in `docs/PRESENTACION_PROYECTO.md`; the 30-second script is in `docs/DEMO_SCRIPT_EN.md`).

---

## Project Name
ORBIT Health

## High-Level Project Summary
ORBIT Health is an offline clinical decision-support and wellbeing tool for a small crew far from Earth, where there is no doctor on board and radio delays or blackouts make real-time help from Earth impossible. It tracks each astronaut's vital signs against both a standard emergency score (NEWS2) and their own 14-day personal baseline, cross-checks the crew with cabin air (CO₂ and O₂) to raise a collective alert, and keeps urgent alerts first when the Earth link returns. Every astronaut also has a private, bilingual (Spanish and English) companion, Nova, that offers emotional support and guided breathing. The alert level is always calculated by written, reviewable rules, never by an AI. It is a prototype and it is not clinically validated.

## Link to Project Demo
**[PUBLIC LINK to the 30-second video or the slide deck]**

## Link to Final Project
**[PUBLIC LINK to the repository or release]** (see item 1 above; it must open without a login)

## Detailed Project Description

**What it does.** A crew of four to six astronauts (one commander and crewmates; there is no flight surgeon) gets:
- *A traffic light per astronaut* (green, yellow, red) from NEWS2 plus combined rules, and a personal baseline that flags quiet deterioration in yellow before a generic threshold would.
- *A collective cabin alert* when CO₂ rises or O₂ drops and two or more crew members show altered signs within 30 minutes.
- *A store-and-forward link to Earth* that models light-time delay for the station, Moon and Mars, keeps every event in a SHA-256 hash chain during a blackout, sends red emergencies first when contact returns, and summarises hundreds of routine readings into one event without deleting the originals.
- *Private wellbeing*: a journal, mood and PHQ-2 screening that never leave the ship and that the commander cannot read; a crisis protocol that checks cabin oxygen first (hypoxia can mimic acute anxiety); and a consent-based, revocable notice to the commander.
- *Nova*, a companion by text and voice in Spanish and English that greets each astronaut by name, remembers the last six messages (never stored on the server), and offers guided breathing. A crisis phrase always receives the written protocol and never goes through a language model.

**How it works.** A FastAPI and SQLite backend and a React interface run on one local server with no internet needed. Thresholds live in JSON files and are cited. Every alert is linked to the NASA Human Research Program hazard it relates to, and a public endpoint shows, risk by risk, what the tool covers. The system can be installed as a web app (PWA), run in a Docker container, or run as a one-file executable for Linux, Windows and macOS.

**What we declare honestly.**
- The crew and the readings are **simulated** and labelled "simulated" everywhere. A real consumer band was tried and uses a proprietary protocol, so it is not supported.
- All thresholds are design assumptions **pending clinical validation**; the interface says so. It does not replace a doctor.
- Of the 17 HRP risks, the tool covers **1 fully, 7 partly and 9 not at all**.
- The local language model we ran is small and its conversation quality is limited; the AI guard blocks invented numbers, medication terms, links and wrong alert levels but does not judge the quality of the text.
- No TLS and no database encryption yet; installing as an app needs localhost or HTTPS.

**What we hope to achieve.** Show that a crew without a doctor can still get explainable, private, immediately available decision support, and that a system can be honest about what it does not know.

**Tools and languages.** Python 3.12, FastAPI, SQLite, TypeScript, React, Vite, ApexCharts, Docker, PyInstaller, GitHub Actions. Optional offline components: Ollama with a small Qwen model for conversation, faster-whisper for speech recognition and Piper for speech synthesis.

## Use of Super Intelligence (SI)
**Tools used in preparing the solution:**
- **Claude (Anthropic), through Claude Code**, working in the repository: wrote the backend, frontend features, tests, scripts, packaging and most of the technical documentation. Work is traceable through the commit trailer `Co-Authored-By: Claude` in the Git history (146 commits by the backend author and 21 by Santiago Antonio Suárez Luna, at the time of writing).
- **GitHub Copilot**: appears as co-author in 2 commits by vzdee, according to the Git trailers.
- **Antigravity (Google DeepMind)**: used by a team member, as stated in his own documents, to organise the executive summary and the English structure of the 5-slide presentation from the team's decisions and implementation.

Commits by the other team members carry no trailer. **[TEAM TO CONFIRM, each of Lourdes Ruiz, vzdee and Mauricio Martinez: whether any SI tool was used beyond what is listed above, including for the demo script or slides.]**

**SI inside the product (optional and disclosed):** Nova can use a small local language model (offline). An optional cloud provider (DeepSeek) can be enabled with an API key; it is off by default, the response says when it was used, and personal data (profile, traits, conversation history, name) are never sent to it. Details: `docs/IA_LOCAL.md`.

**How SI was and was not used for the idea:** The concept and the approach come from the team's own analysis of the challenge statement and the resources linked to it (the NASA Human Research Program hazard and risk pages, the ARCHeR study description and related public documents). That analysis defined the problem: offline decision support for a crew without a doctor, explainable rules, and privacy of mental-health data. SI tools were used afterwards to help implement and document that approach. SI was not used to come up with the idea of how to solve the challenge.

**Images and media:** No image or video in the project was generated with SI. Two points to disclose for completeness:
- The **app icons** (the orbit and planet logo) were drawn by a small script (`scripts/generar_iconos.py`) written with Claude Code; it draws shapes programmatically and does not use an image-generation model.
- **Nova's spoken replies** are synthesised at runtime by a neural text-to-speech model (Piper) when voice is switched on, and speech is recognised by a neural model (faster-whisper). No pre-generated audio is included in the repository. If the demo video features Nova's voice, say so in the video description.
The origin and licence of the astronaut illustration and the skeleton and muscle layers are still to be confirmed (see item 2 above). No NASA logos or branding were generated or modified.

**Code and data:** acknowledged here and in the repository (`docs/SI_DISCLOSURE.md`, commit trailers).

## NASA Data
We used these NASA resources (all public pages and records; no private data):
- NASA Human Research Program, *Five Hazards of Human Spaceflight* and *Risks of Human Spaceflight*, and the individual risk pages (sleep and irregular schedules, behavioral conditions and psychiatric disorders, reduced cardiorespiratory and musculoskeletal fitness, spaceflight-induced bone changes, gravity fields, hostile closed environments, among others). They define the indicators, the hazard and risk mapping, and the plain-language explanations, which quote NASA's own wording and link to the page.
- NASA's description of the **ARCHeR** study (actigraphy during Artemis) and the NASA technical report on continuous versus intermittent actigraphy (NTRS 20220014774), which motivated the sleep metrics (duration, efficiency, time awake).
- NASA images: the Apollo 17 "Blue Marble" photograph and the NASA Blue Marble equirectangular map of the Earth (public domain, credited in the repository).

## Space Agency Partner Data and Other References
**Space agency partner:** Canadian Space Agency, *radiation monitoring for astronaut health* (news release, February 2026), cited for the radiation-dose indicator.

**Other data and references:**
- Royal College of Physicians, **NEWS2** (National Early Warning Score 2), for the scoring scheme.
- **BIDMC PPG and Respiration Dataset v1.0.0** (PhysioNet, Open Data Commons Attribution License v1.0, DOI 10.13026/C2208R), used only to give the simulated demo realistic variability. These are records of hospital patients, not astronauts; attribution is in `data/physionet/ATRIBUCION.md`.
- **Open-source software:** FastAPI, Uvicorn, Pydantic, httpx, SQLite, React, Vite, ApexCharts, Docker, PyInstaller. Optional offline components, not bundled in the repository and each under its own licence: Ollama, Qwen2.5 models, faster-whisper, Piper and its Spanish (Mexico) and English voices.
- **Images:** "Circulatory System no tags.svg" by LadyofHats (Wikimedia Commons, public domain). The Space Apps logo is used only to identify participation in the challenge. **[TEAM TO CONFIRM or replace: astronaut illustration, skeleton and muscle layers; origin and licence are pending.]**
