# ORBIT Health — project summary

**Challenge:** Create Health Monitoring Software for Astronauts on Space Missions.

## The problem
On a long mission, communication with Earth is delayed or interrupted and there is no medical evacuation. The crew has to assess its own health and decide what to do while Earth is still unable to answer. A message to Mars can take up to about 20 minutes each way (design assumption, see `backend/app/datos/enlace.json`).

## What ORBIT Health does
- **Decides on board, instantly and without a network.** Vital signs are scored with the published NEWS2 early-warning scheme plus rules that combine signals (for example, high cabin CO₂ with several crew members affected). Every result is explainable and every threshold lives in one editable file.
- **Tells the crew what to do now.** Each alert returns plain procedural steps (repeat the measurement, notify the flight surgeon or commander, measure again in N minutes). It never suggests treatment or medication.
- **Teaches while it monitors.** Every indicator has a short explanation: what it is, why it is measured, how to measure it and what spaceflight changes about it, with a link to the official source.
- **Says what NASA says, and what it does not.** Where NASA's own pages state a measure (for example exercise 6 to 7 days a week and 1.5 hours of aerobic work on the station, or LED light to simulate Earth's day and night), the tool shows it with the verbatim quote and the link. Where the page gives no guidance (blood glucose, hypoxia countermeasures), it says so instead of inventing any. Our own common-sense tips are labelled as such.
- **Knows where the crew is.** Environments (transit, station, Moon base, Mars base, rover) carry their gravity, and the bone-loss estimate is shown only in microgravity, because NASA gives that figure for 4 to 6 month missions in microgravity and none for partial gravity.
- **Built on NASA's hazard framework.** The five Human Research Program hazards and the 17 listed risks are part of the product: every alert is linked to the hazard it relates to, and a public endpoint shows, risk by risk, what the tool covers. Honest count: 1 risk fully covered, 7 partially, 9 not covered.
- **Adapts how it talks to each astronaut.** Each crew member chooses a tone (direct or warm), a level of detail (brief or complete) and how often to be reminded. This changes the wording only, never the alert level, the priority or the essential warnings, and nothing is inferred from the diary or the mood score.
- **Compares each person with themselves.** A rolling personal baseline flags deviations, because "normal" in microgravity is not "normal" on Earth.
- **Survives the isolation.** A store-and-forward queue holds events during a blackout and releases the most urgent first when the link returns. Delivery and the round-trip confirmation are simulated with configurable delay per environment. A hash chain makes tampering detectable.
- **Protects privacy.** The personal diary, the PHQ-2 answers and the daily mood score belong to their owner only, and none of them is ever queued for Earth. The single way out is a notice the crew member chooses to send: with explicit, revocable consent, a short notice (its type and level plus an optional message, never the diary or the score) can reach the flight surgeon or the commander. Creating, revoking and handling it is audited.
- **Rewards consistency without pressure.** A light streak counts the days with all five vital signs recorded; it does not break while today is still in progress.
- **Heals itself.** On start-up it verifies its database, restores the last valid backup if needed and keeps automatic backups, because nobody on board can repair it.

## Indicators covered
Blood pressure, heart rate, respiratory rate, blood oxygen, body temperature, consciousness level, blood glucose, cabin CO₂, cabin oxygen, accumulated radiation dose, hours of sleep, minutes of exercise, and mood.

## Built for the environment
Runs fully offline from a single local server. Optional local authentication (switched on with a setting; off by default for a single-station demo) by PIN with temporary lockouts, a recovery code and audit trail, designed for a small crew with no internet, where any member may need to log vital signs for an incapacitated colleague.

## Sources we used
- NASA Human Research Program, [Five Hazards of Human Spaceflight](https://www.nasa.gov/hrp/hazards) and [Risks of Human Spaceflight](https://www.nasa.gov/hrp/risks/), plus the ARCHeR study description, as the framework the tool is organised around. The hazard-to-indicator association is our own design decision, not an official NASA classification.
- Canadian Space Agency, [radiation monitoring for astronaut health](https://www.canada.ca/en/space-agency/news/2026/02/canadian-space-radiation-technology-to-support-health-and-safety.html).
- Royal College of Physicians, NEWS2, for the scoring scheme.
- [BIDMC PPG and Respiration Dataset v1.0.0](https://physionet.org/content/bidmc/1.0.0/) (PhysioNet, Open Data Commons Attribution License v1.0, DOI 10.13026/C2208R), to give the demo realistic variability. These are records of critically ill hospital patients, not of astronauts or healthy people.

## Honest limitations
- The live mission shown in the demo is a script: its values are invented, although they travel through the same sensor channel a real band would use. They are stored, shown in the history and sent to Earth tagged as `simulated`, never as real sensor data.
- This is a **prototype** that supports decisions. It does not replace the flight surgeon.
- **All thresholds are design assumptions pending clinical validation.** The interface says so on screen.
- Vital signs are entered by hand, through a simulated device or, for heart rate only, through a Bluetooth bridge. The bridge is tested with simulated packets and against the real server. A real consumer band (IDW26, Veryfit app) was tried: it connects but exposes no standard services (proprietary protocol), so it is **not supported**. Other vitals from consumer bands would need vendor-specific protocols.
- The "with and without ORBIT" timeline is an illustration with explicit assumptions, not a measurement.
- Only 8 of the 17 HRP risks have any indicator behind them, and only hypoxia is covered directly.
- The adaptive assistant is preference-based personalisation, not a model that learns personalities. A local language model that rephrases the texts is future work.
- No encryption at rest and no TLS on the cabin network yet.
