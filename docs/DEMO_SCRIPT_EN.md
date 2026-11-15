# ORBIT Health: demo script (English)

Challenge: **Health Monitoring Software**. Two formats are prepared; the team picks one (confirm the limits in the official 2026 Project Submission Guide: video up to 30 s with English subtitles, or up to 7 slides in English).

Everything shown comes from the running system. The crew is **simulated** and must be labelled as such on screen.

## Option A: 30-second video (about 70 spoken words)

| Time | On screen | Voice-over / subtitle |
|---|---|---|
| 0-4 s | Dashboard, four crew members, all green | "Far from Earth, a crew can't wait for ground control." |
| 4-10 s | Start the live mission (`POST /api/demo/simulacion/iniciar`); cabin CO₂ rises, one crew member turns yellow against their own baseline | "ORBIT Health watches each astronaut against their own baseline, and the cabin too." |
| 10-16 s | Collective alert; link-loss banner ("Eclipse mode") | "When several people are affected, it flags the cabin, not just the person. When the link drops, it keeps working." |
| 16-23 s | Queue panel: urgent events first, routine events summarised after the link returns | "Alerts wait on board and go first when contact returns. Routine data is summarised." |
| 23-27 s | Voice/assistant bubble, "AI-generated" label | "A local assistant explains the alert. It never decides it, and crisis messages always follow a written protocol." |
| 27-30 s | Title card: team name, challenge, "Simulated crew. Offline-first." | "ORBIT Health. Decision support that works without the internet." |

## Option B: 7 slides (title slide counts)

| # | Slide | Content |
|---|---|---|
| 1 | Title | ORBIT Health; **[TEAM NAME]**; **[MEMBER NAMES]**; challenge: Health Monitoring Software |
| 2 | The problem | Crew health far from Earth: communication delay and blackouts, no real-time ground support, five human-health hazards defined by NASA's Human Research Program |
| 3 | The solution | Offline clinical decision support: transparent rules (NEWS2-based), personal baselines, collective cabin alerts, store-and-forward queue with integrity chain |
| 4 | How NASA resources made it possible | NASA HRP hazard and risk pages (sleep, behavioral health, gravity fields, radiation, hostile closed environments) shaped the indicators and the explanations, with verbatim quotes and links; the ARCHeR actigraphy study motivated the sleep metrics (duration, efficiency, time awake). Calibration signals: BIDMC PPG and Respiration Dataset (PhysioNet), not NASA data |
| 5 | Demo | Screenshots: dashboard, mission story, queue after the blackout |
| 6 | Responsible design | Thresholds are design assumptions pending clinical validation (stated on screen); mental-health notes stay private; AI never sets alert levels, crisis goes to a written protocol, outputs are checked and labelled; simulated data is tagged `simulated` |
| 7 | Limits and next steps | Not clinically validated; a real consumer band was tried but uses a proprietary protocol (not supported); optional external AI provider exists for development only. Next: clinical review, standard-protocol sensors, encryption and TLS |

## Claims to avoid
- No claim of clinical validity, accuracy figures or "real-time NASA monitoring": NASA's ARCHeR page only says actigraphy is collected during the mission.
- No claim that the crew or readings are real.
- Show the AI labels and the "simulated" tags on screen: judges look for AI disclosure (see `SI_DISCLOSURE.md`).
