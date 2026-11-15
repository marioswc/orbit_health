# Formulario de NASA Space Apps: contenido listo para pegar

Sigue el orden y los campos **reales** del formulario (Project Summary, Project Links, Project Information, Verification). Todo lo que se pega está en **inglés**, como exige la guía. Lo que está en **[CORCHETES]** solo lo puede poner el equipo.

## PRIMERO: lo que bloquea el envío (resolver antes de pegar nada)

| # | Bloqueo | Qué hacer |
|---|---|---|
| 1 | El repositorio es **privado** y el formulario exige enlaces **públicos, sin login** (para el premio global también) | Mario decide: hacer público el repositorio, o subir un Release público, o un enlace público de Drive. Probarlo en una ventana privada del navegador |
| 2 | **"Confirm All Work is Original"**: afirma que no usaron material con derechos que no tengan permiso de usar. `astronauta.svg`, `esqueleto.webp` y la capa de músculos vienen de un banco de imágenes **con marca de agua**, con origen y licencia "pendiente de confirmar" | **No marquen esa casilla si no tienen permiso.** Opciones: confirmar la licencia, reemplazar esas imágenes por otras propias o libres, o quitarlas |
| 3 | El demo (video de 30 s o menos, o máximo 7 diapositivas) no está subido | Subirlo a un lugar público sin contraseña. Guion: `docs/DEMO_SCRIPT_EN.md`; estructura de 5 diapositivas: `docs/PRESENTACION_PROYECTO.md` |
| 4 | Los demás integrantes no han confirmado qué herramientas de IA usaron | Cada quien revisa lo que el texto dice de él (ver "Use of SI" abajo) |

Plazo: **domingo 15-nov, 11:59 pm hora local de su evento.** Se puede **guardar** muchas veces ("Save Progress"), pero solo cuenta el último **"Submit for Judging"**. Cuidado con el candado "Lock": otro integrante puede quitarlo y sobrescribir.

---

## PROJECT SUMMARY

### Project Name
```
ORBIT Health
```

### Summary * (tope 1500 caracteres; este mide 1047, 172 palabras)
```
ORBIT Health is an offline clinical decision-support and wellbeing tool for a small crew far from Earth, where there is no doctor on board and communication delays or blackouts make real-time help from Earth impossible. It follows each astronaut's vital signs against both the NEWS2 emergency score and their own 14-day personal baseline, cross-checks the crew with cabin CO2 and O2 to raise a collective alert, and keeps urgent alerts first when the Earth link returns. Every astronaut also has Nova, a private bilingual (Spanish and English) companion for emotional support and guided breathing. The alert level is always calculated by written, reviewable rules, never by an AI. The tool maps the NASA Human Research Program hazards and risks and states honestly what it covers: 1 of 17 risks fully, 7 partly, 9 not covered. The crew and the readings are simulated and the thresholds are design assumptions pending clinical validation. It runs from one local server, as an installable web app, as a Docker container or as a one-file desktop app.
```

---

## PROJECT LINKS (enlaces completos, con `https://`, públicos y sin login)

### Project Demonstration *
**[URL PÚBLICO del video (30 s o menos, con subtítulos en inglés) o de las diapositivas (máximo 7, en inglés)]**
Para premio global: debe abrirse sin contraseña ni registro, y no pasar de 7 diapositivas o 30 segundos.

### Project *
**[URL PÚBLICO del proyecto final]** (ver bloqueo 1). Si es el repositorio: `https://github.com/marioswc/orbit_health`, **solo cuando sea público.**

---

## PROJECT INFORMATION

### Project Details * (editor de texto enriquecido: pega esto)
```
WHAT IT DOES
A crew of four to six astronauts (one commander and crewmates; there is no flight surgeon) gets:
- A traffic light per astronaut (green, yellow, red) from the NEWS2 early-warning score plus combined rules, and a personal 14-day baseline that flags quiet deterioration in yellow before a generic threshold would.
- A collective cabin alert when CO2 rises or O2 drops and two or more crew members show altered signs within 30 minutes.
- A store-and-forward link to Earth that models light-time delay for the station, the Moon and Mars, seals every event in a SHA-256 hash chain during a blackout, sends red emergencies first when contact returns, and summarises hundreds of routine readings into one event without deleting the originals.
- Private wellbeing: a journal, mood and PHQ-2 screening that never leave the ship and that the commander cannot read; a crisis protocol that checks cabin oxygen first (hypoxia can mimic acute anxiety); and a consent-based, revocable notice to the commander.
- Nova, a companion by text and voice in Spanish and English. It greets each astronaut by name, remembers the last six messages (never stored on the server) and offers guided breathing. A crisis phrase always receives the written protocol and never goes through a language model.

HOW IT WORKS
A FastAPI and SQLite backend and a React interface run on one local server with no internet needed. Clinical thresholds live in cited JSON files. Every alert is linked to the NASA Human Research Program hazard it relates to, and a public endpoint shows, risk by risk, what the tool covers. An optional small language model runs inside the program (llama.cpp) for Nova's conversation; an AI guard rejects any model output with invented numbers, medication terms, links or wrong alert levels, and the model never decides an alert. It can be used as an installable web app (PWA), in a Docker container, or as a one-file desktop app for Linux, Windows and macOS that opens its own window.

BENEFITS AND INTENDED IMPACT
A crew without a doctor can still get explainable, private, immediately available decision support, and the system is honest about what it does not know. The same design applies to remote or low-connectivity settings on Earth.

HOW IT IS CREATIVE
It treats the communication delay itself as a design input (delay model, blackout queue, urgent-first dispatch), correlates individual health with the shared cabin air, personalises support through each astronaut's own baseline and chosen interests instead of a generic model, and keeps the clinical decision deterministic and auditable while using AI only for companionship, with safeguards.

FACTORS WE CONSIDERED
No doctor on board; no internet; privacy of mental-health data (even from the commander); transparency (every AI answer is labelled, simulated data is tagged "simulated"); security (PIN login with lockouts, audit chain, rate limits, prompt hardening); and what NASA's pages say and do not say (we quote them and do not invent figures).

TOOLS AND LANGUAGES
Python 3.12, FastAPI, SQLite, TypeScript, React, Vite, ApexCharts, Docker, PyInstaller, GitHub Actions. Optional offline components: llama.cpp with a small Qwen2.5 model, faster-whisper for speech recognition and Piper for speech synthesis.

HONEST LIMITATIONS
- The crew and the readings are simulated and labelled "simulated". A real consumer wristband was tried and uses a proprietary protocol, so it is not supported.
- All thresholds are design assumptions pending clinical validation; the interface says so on screen. This is a prototype and it does not replace a doctor.
- Of the 17 NASA HRP risks, the tool covers 1 fully, 7 partly and 9 not at all.
- The small language model has limited conversation quality; the AI guard blocks invented numbers, medication terms, links and wrong alert levels but does not judge the quality of the text.
- No TLS and no database encryption yet; installing as an app needs localhost or HTTPS.

USE OF SUPER INTELLIGENCE (SI), ACKNOWLEDGEMENT
- Claude (Anthropic), through Claude Code, was used to write most of the backend, several frontend features, the automated tests, the scripts, the packaging and most of the technical documentation. The work is traceable through the "Co-Authored-By: Claude" trailer in the Git history.
- GitHub Copilot appears as co-author in a small number of commits by one team member.
- Antigravity (Google DeepMind) was used by one team member to organise the executive summary and the English structure of the presentation.
- Inside the product: Nova can use a small local language model (offline). An optional cloud provider (DeepSeek) can be enabled with an API key; it is off by default, the answer says when it was used, and personal data (profile, traits, conversation history, name) are never sent to it.
- Audio: when voice is switched on, Nova's spoken replies are synthesised at runtime by a neural text-to-speech model (Piper) and speech is recognised by a neural model (faster-whisper). No pre-generated audio is stored in the repository. [ADD IF THE DEMO VIDEO USES NOVA'S VOICE: "The voice heard in the demo video is Nova's SI-synthesised voice."]
- Images and video: no image or video in the project was generated with SI. The app icons are drawn by a small script that was written with Claude Code (it draws shapes programmatically and does not use an image-generation model).
- The project idea and approach come from the team's own analysis of the challenge statement and its resources (NASA Human Research Program pages, the ARCHeR study description and related public documents). SI was used afterwards to help implement and document it; it was not used to come up with the idea of how to solve the challenge.
- No NASA logos or branding were generated or modified. Full disclosure: docs/SI_DISCLOSURE.md in the repository.
```

### Use of Super Intelligence (SI) * (casillas "Select options")
No conozco los nombres exactos de las opciones del formulario; elige las que correspondan a esto:

| Marca | Motivo |
|---|---|
| **Sí: código** (y datos, si hay opción) | Claude Code, GitHub Copilot y Antigravity ayudaron con código y documentación |
| **Sí: texto / documentación**, si existe la opción | Documentación y textos redactados con ayuda de IA |
| **Sí: audio**, **solo si** el video o el producto mostrado usa la voz de Nova | La voz hablada de Nova es sintética (Piper). Si el demo no la usa, puedes no marcarlo, pero lo dejé declarado arriba |
| **No: imágenes y video** | Según el equipo, ninguna imagen ni video se generó con IA. (Los iconos los dibuja un script, no un modelo de imágenes) |
| **NO marcar "I did not use SI"** | Sería falso |

Esta respuesta, según el formulario, **no la ven los jueces**; sí ven los indicadores dentro del proyecto, por eso el reconocimiento va también en *Project Details* (arriba), en `docs/SI_DISCLOSURE.md` y en el historial de commits.

### NASA Data * (para premio global debe haber al menos un recurso de NASA)
Formato: **Link Text** / **Link Url**. Usa "Add New Link" para cada fila. Todos estos enlaces están en los datos del propio proyecto (cada alerta y explicación cita su página).

| Link Text | Link Url |
|---|---|
| NASA HRP: Five Hazards of Human Spaceflight | https://www.nasa.gov/hrp/hazards |
| NASA HRP: Risks of Human Spaceflight | https://www.nasa.gov/hrp/risks/ |
| NASA HRP Hazard: Space Radiation | https://www.nasa.gov/hrp/hazard-space-radiation/ |
| NASA HRP Hazard: Isolation and Confinement | https://www.nasa.gov/hrp/hazard-isolation-and-confinement/ |
| NASA HRP Hazard: Distance from Earth | https://www.nasa.gov/hrp/hazard-distance-from-earth/ |
| NASA HRP Hazard: Gravity Fields | https://www.nasa.gov/hrp/hazard-gravity-fields/ |
| NASA HRP Hazard: Hostile and Closed Environments | https://www.nasa.gov/hrp/hazard-hostile-closed-environments/ |
| NASA ARCHeR study (Artemis crew health and readiness, actigraphy) | https://www.nasa.gov/reference/archer |
| NASA Risk of Inadequate Sleep and Irregular Schedules | https://www.nasa.gov/reference/risk-from-inadequate-sleep-and-irregular-schedules/ |
| NASA Risk of Behavioral Conditions and Psychiatric Disorders | https://www.nasa.gov/reference/risk-of-behavioral-conditions-and-psychiatric-disorders/ |
| NASA Risk of Hypoxia | https://www.nasa.gov/reference/risk-of-hypoxia/ |
| NASA Risk of Reduced Cardiorespiratory and Musculoskeletal Fitness | https://www.nasa.gov/reference/risk-of-reduced-cardiorespiratory-and-musculoskeletal-fitness/ |
| NASA Risk of Spaceflight-Induced Bone Changes | https://www.nasa.gov/reference/risk-of-spaceflight-induced-bone-changes/ |
| NASA NTRS 20220014774: continuous vs intermittent actigraphy in astronaut crews | https://ntrs.nasa.gov/citations/20220014774 |
| The Earth seen from Apollo 17, "Blue Marble" (NASA photograph, public domain) | https://commons.wikimedia.org/wiki/File:The_Earth_seen_from_Apollo_17.jpg |
| Land, ocean, ice 2048, NASA Blue Marble map (public domain) | https://commons.wikimedia.org/wiki/File:Land_ocean_ice_2048.jpg |

**Opcional (el sistema también enlaza estas 10 páginas de riesgos HRP; agrégalas si hay tiempo):**
- https://www.nasa.gov/reference/risk-of-altered-immune-system-responses/
- https://www.nasa.gov/reference/risk-of-altered-sensorimotor-and-vestibular-function/
- https://www.nasa.gov/reference/risk-of-cardiovascular-adaptations/
- https://www.nasa.gov/reference/risk-of-decompression-sickness/
- https://www.nasa.gov/reference/risk-of-host-microorganism-interactions/
- https://www.nasa.gov/reference/risk-of-inadequate-food-and-nutrition/
- https://www.nasa.gov/reference/risk-of-inadequate-systems-operations-support/
- https://www.nasa.gov/reference/risk-of-inadequate-teamwork/
- https://www.nasa.gov/reference/risk-of-injury-and-compromised-performance-from-extravehicular-activity-eva/
- https://www.nasa.gov/reference/risk-of-injury-from-dynamic-loads/
- https://www.nasa.gov/reference/risk-of-radiation-induced-cancers/
- https://www.nasa.gov/reference/risk-of-spaceflight-associated-neuro-ocular-syndrome-sans/

### Space Agency Partner & Other Data
Aquí va **todo** lo demás que usaron (el formulario pide también código, texto e imágenes, aunque sean abiertos). Todos estos enlaces abrieron al comprobarlos.

| Link Text | Link Url |
|---|---|
| Canadian Space Agency: Canadian space radiation technology to support health and safety (news release, 26 Feb 2026) | https://www.canada.ca/en/space-agency/news/2026/02/canadian-space-radiation-technology-to-support-health-and-safety.html |
| Royal College of Physicians: National Early Warning Score (NEWS2) | https://www.rcp.ac.uk/improving-care/resources/national-early-warning-score-news-2/ |
| BIDMC PPG and Respiration Dataset v1.0.0 (PhysioNet, ODC-By 1.0), used only to give the simulated demo realistic variability | https://physionet.org/content/bidmc/1.0.0/ |
| BIDMC dataset DOI | https://doi.org/10.13026/C2208R |
| Circulatory System no tags.svg by LadyofHats (Wikimedia Commons, public domain) | https://commons.wikimedia.org/wiki/File:Circulatory_System_no_tags.svg |
| FastAPI (web framework) | https://fastapi.tiangolo.com |
| Uvicorn (server) | https://uvicorn.dev |
| Pydantic (data validation) | https://docs.pydantic.dev |
| SQLite (database) | https://www.sqlite.org |
| React (interface) | https://react.dev |
| Vite (build tool) | https://vite.dev |
| ApexCharts (charts) | https://apexcharts.com |
| PyInstaller (one-file desktop app) | https://pyinstaller.org |
| Docker (container) | https://www.docker.com |
| llama.cpp (embedded AI engine, optional) | https://github.com/ggml-org/llama.cpp |
| llama-cpp-python (bindings, optional) | https://github.com/abetlen/llama-cpp-python |
| Qwen2.5 1.5B Instruct GGUF (small language model, Apache-2.0, optional) | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF |
| Ollama (alternative local model server, optional) | https://ollama.com |
| faster-whisper (speech recognition, optional) | https://github.com/SYSTRAN/faster-whisper |
| faster-whisper small model (optional) | https://huggingface.co/Systran/faster-whisper-small |
| Piper TTS (speech synthesis, optional) | https://pypi.org/project/piper-tts/ |
| Piper voices, Spanish (Mexico) and English (optional) | https://huggingface.co/rhasspy/piper-voices |
| NASA Space Apps Challenge logo (used only to identify participation in the challenge) | https://assets.spaceappschallenge.org/media/images/Space_Apps_Logo_Color_and_White.width-440.jpegquality-60.png |

**Falta una fila que SOLO el equipo puede llenar (bloqueo 2):** el origen y la licencia del dibujo del astronauta, del esqueleto y de los músculos. Si no hay permiso, **reemplazarlos o quitarlos antes de marcar "Confirm All Work is Original"**, y no agregar una fila con un origen que no se pueda comprobar.

---

## PROJECT SUBMISSION VERIFICATION
- **Agree to Terms and Conditions**: léanlo y márquenlo.
- **Confirm All Work is Original**: **solo si** resolvieron el bloqueo 2 y todos los recursos externos están listados arriba. Es una declaración del equipo; no la marque yo ni nadie por ustedes.
- Luego **Save Progress** y, al final, **Submit for Judging** (verán una barra de confirmación arriba). Se puede reenviar hasta las 11:59 pm; cuenta el último envío. Después de esa hora no hay excepciones.
