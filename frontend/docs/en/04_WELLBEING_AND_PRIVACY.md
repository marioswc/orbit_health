# 04 — Wellbeing & Mental Health Privacy

## What problem existed
Mental health data (daily mood, personal journal entries, depression screening) is highly sensitive: it must never be mixed with general telemetry or transmitted to Earth without explicit permission. In addition, low cabin oxygen can trigger or worsen psychological distress.

## How it was solved
- **Strict privacy boundary ([BienestarPage.tsx](../../src/features/bienestar/routes/BienestarPage.tsx), commits `901bc30`, `c9f1081`, `eca3fc9`):**
  - The header clearly communicates that mood, journal, and screening stay on the local device and **never enter the Earth-bound queue**.
  - Moving assistant preferences to the Assistant tab (`feef45a`) kept Wellbeing focused strictly on private mental health support.
- **Daily mood & searchable journal (commits `b2b942c`, `c9f1081`):**
  - Quick 1-to-5 mood check-in with a personal trend chart and gentle notices when mood shifts from the recent baseline.
  - Personal journal with keyword search, month/period filters, and a clean modal reader.
- **PHQ-2 screening, cabin O₂ check & crisis protocol (commit `ce363f8`):**
  - If screening is positive or the crew member reports an acute crisis, immediate support steps appear alongside a cabin oxygen (`% O₂`) check to rule out environmental hypoxia.
  - **Explicit, revocable consent:** the crew member chooses whether to notify the onboard physician (with an optional short note) and can **withdraw consent** at any time.
