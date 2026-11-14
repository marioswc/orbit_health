# ORBIT Health — project summary

**Challenge:** Create Health Monitoring Software for Astronauts on Space Missions.

## The problem
On a long mission, communication with Earth is delayed or interrupted and there is no medical evacuation. The crew has to assess its own health and decide what to do while Earth is still unable to answer. A message to Mars can take up to about 20 minutes each way (design assumption, see `backend/app/datos/enlace.json`).

## What ORBIT Health does
- **Decides on board, instantly and without a network.** Vital signs are scored with the published NEWS2 early-warning scheme plus rules that combine signals (for example, high cabin CO₂ with several crew members affected). Every result is explainable and every threshold lives in one editable file.
- **Tells the crew what to do now.** Each alert returns plain procedural steps (repeat the measurement, notify the flight surgeon or commander, measure again in N minutes). It never suggests treatment or medication.
- **Teaches while it monitors.** Every indicator has a short explanation: what it is, why it is measured, how to measure it and what spaceflight changes about it, with a link to the official source.
- **Built on NASA's hazard framework.** The five Human Research Program hazards and the 17 listed risks are part of the product: every alert is linked to the hazard it relates to, and a public endpoint shows, risk by risk, what the tool covers. Honest count: 1 risk fully covered, 7 partially, 9 not covered.
- **Adapts how it talks to each astronaut.** Each crew member chooses a tone (direct or warm), a level of detail (brief or complete) and how often to be reminded. This changes the wording only, never the alert level, the priority or the essential warnings, and nothing is inferred from the diary or the mood score.
- **Compares each person with themselves.** A rolling personal baseline flags deviations, because "normal" in microgravity is not "normal" on Earth.
- **Survives the isolation.** A store-and-forward queue holds events during a blackout and releases the most urgent first when the link returns. Delivery and the round-trip confirmation are simulated with configurable delay per environment. A hash chain makes tampering detectable.
- **Protects privacy.** The personal diary, the PHQ-2 mood screening and the daily mood score belong to their owner only. They are never queued for Earth and no role can read them.
- **Heals itself.** On start-up it verifies its database, restores the last valid backup if needed and keeps automatic backups, because nobody on board can repair it.

## Indicators covered
Blood pressure, heart rate, respiratory rate, blood oxygen, body temperature, consciousness level, blood glucose, cabin CO₂, accumulated radiation dose, hours of sleep, minutes of exercise, and mood.

## Built for the environment
Runs fully offline from a single local server. Optional local authentication (switched on with a setting; off by default for a single-station demo) by PIN with temporary lockouts, a recovery code and audit trail, designed for a small crew with no internet, where any member may need to log vital signs for an incapacitated colleague.

## Sources we used
- NASA Human Research Program, [Five Hazards of Human Spaceflight](https://www.nasa.gov/hrp/hazards) and [Risks of Human Spaceflight](https://www.nasa.gov/hrp/risks/), plus the ARCHeR study description, as the framework the tool is organised around. The hazard-to-indicator association is our own design decision, not an official NASA classification.
- Canadian Space Agency, [radiation monitoring for astronaut health](https://www.canada.ca/en/space-agency/news/2026/02/canadian-space-radiation-technology-to-support-health-and-safety.html).
- Royal College of Physicians, NEWS2, for the scoring scheme.
- [BIDMC PPG and Respiration Dataset v1.0.0](https://physionet.org/content/bidmc/1.0.0/) (PhysioNet, Open Data Commons Attribution License v1.0, DOI 10.13026/C2208R), to give the demo realistic variability. These are records of critically ill hospital patients, not of astronauts or healthy people.

## Honest limitations
- This is a **prototype** that supports decisions. It does not replace the flight surgeon.
- **All thresholds are design assumptions pending clinical validation.** The interface says so on screen.
- Vital signs are entered by hand or through a simulated device; there is no integration with real sensors yet.
- The "with and without ORBIT" timeline is an illustration with explicit assumptions, not a measurement.
- Only 8 of the 17 HRP risks have any indicator behind them, and only hypoxia is covered directly.
- The adaptive assistant is preference-based personalisation, not a model that learns personalities. A local language model that rephrases the texts is future work.
- No encryption at rest and no TLS on the cabin network yet.
