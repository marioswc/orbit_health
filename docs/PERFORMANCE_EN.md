# Measured response times

Measured with `scripts/medir_tiempos.py`: it starts the real server, sends 300 requests per operation over HTTP on localhost against a temporary SQLite database, and prints percentiles. Reproduce with `backend/.venv/bin/python scripts/medir_tiempos.py 300`.

| Operation | Median | 95th percentile | Worst |
|---|---|---|---|
| Register a reading (classify, store, queue the event) | 4.7 ms | 6.3 ms | 6.9 ms |
| Read a crew member's current status | 4.4 ms | 5.8 ms | 8.0 ms |
| Read a time series for a chart | 3.3 ms | 4.3 ms | 5.7 ms |
| Build the exportable report | 6.6 ms | 10.4 ms | 14.8 ms |

Machine: Linux x86_64, 8 CPUs, Python 3.12.3 (a development laptop, **not flight hardware**).

## What this does and does not show
- It shows that the on-board decision is local and takes milliseconds: nothing waits for a network or for Earth.
- It does **not** measure concurrent users, a slower flight computer, the browser rendering time, or a large database. Those numbers should not be inferred from this table.
- The simulated link delay (seconds to minutes) is a separate, configurable model and is not part of these figures.
