# Measured response times

Measured with `scripts/medir_tiempos.py`: it starts the real server, sends 300 requests per operation over HTTP on localhost against a temporary SQLite database, and prints percentiles. Reproduce with `backend/.venv/bin/python scripts/medir_tiempos.py 300`.

| Operation | Median | 95th percentile | Worst |
|---|---|---|---|
| Register a reading (classify, store, queue the event) | 4.6 ms | 5.9 ms | 14.6 ms |
| Read a crew member's current status | 4.1 ms | 5.2 ms | 6.9 ms |
| Read a time series for a chart | 3.4 ms | 4.4 ms | 5.6 ms |
| Build the exportable report | 5.8 ms | 6.9 ms | 21.2 ms |

Re-measured after the later features were added; results vary slightly from run to run.

Machine: Linux x86_64, 8 CPUs, Python 3.12.3 (a development laptop, **not flight hardware**).

## What this does and does not show
- It shows that the on-board decision is local and takes milliseconds: nothing waits for a network or for Earth.
- It does **not** measure concurrent users, a slower flight computer, the browser rendering time, or a large database. Those numbers should not be inferred from this table.
- The simulated link delay (seconds to minutes) is a separate, configurable model and is not part of these figures.


---

> **AI Signature & Justification (SI Disclosure):**
> - **Tool used:** **Claude (Anthropic)** via **Claude Code**.
> - **Justification:** Used as a technical assistant during the hackathon to draft and structure technical documentation, record architectural decisions, and maintain traceability with the source code and public NASA references, under the human team's conceptual definition, review, and validation (in compliance with *NASA Space Apps Challenge* rules).
