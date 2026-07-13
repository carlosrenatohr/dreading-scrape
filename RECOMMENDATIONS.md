# Recommendations — dreading-scrape

Prioritized backlog for reviving this scraper. References use `file:line` from the current tree.

## Already addressed in this pass
- Redis over TLS for Upstash, toggleable via `UPSTACK_SSL` (`services/db_cache.py`).
- Cache is keyed by each reading's own date instead of a single global "today" key (`lectura.py` `send_data_to_db`).
- DST-aware Spain time via `ZoneInfo("Europe/Madrid")` instead of a hardcoded UTC+1 (`lectura.py`).
- `run_from_date` now honors its `start_date`/`end_date` arguments (`lectura.py`).
- Parser skips sections/pages with no reading body instead of crashing (`services/bs_helper.py`).
- Configurable Mongo URI (`DB_URI`) and database name (`DB_NAME`) so the same code runs against local Docker or Atlas (`services/db.py`).
- Dockerized: `Dockerfile` + `docker-compose.yml` (local Mongo + Redis) for zero-credential end-to-end runs.
- Dropped redundant deps (`bs4`, `load-dotenv`); `.DS_Store` ignored; `.env.demo` cleaned and documented.

## P0 — blocks fresh data (the source site changed)
1. **The source website was restructured.** As of 2026-07:
   - `…/calendario-lecturas/evangelio-del-dia/hoy` now `301`-redirects to `https://www.ciudadredonda.org/evangelio-lecturas-hoy/`.
   - The `?f=YYYY-MM-DD` date parameter is **ignored** — every date resolves to the same single "today" page. Per-date/date-range fetching (`run_from_last_week`, `run_from_next_week` in `lectura.py`) is no longer supported by the site.
   - The reading markup changed: there is no longer a `<time datetime=…>`, `<section>`, or `div.texto_palabra`. Content now lives under `<article>` / `.entry-content`.
   **Action:** update `URL`/`URL_TODAY` to the new path (follow redirects), rewrite `services/bs_helper.py` selectors for the new DOM, and decide a new dating strategy (e.g. run daily and stamp with the run date, or find a JSON/feed endpoint). The bundled `lectura.html` remains a valid fixture for the *old* layout only.

## P1 — correctness & reliability
2. **Fail loudly.** `MongoUp.connect` swallows exceptions and leaves `_client = None` (`services/db.py:20`), so later calls raise `AttributeError` and CI can report success on a no-op run. Raise on connection failure and exit non-zero.
3. **Replace `print` with `logging`** and return/propagate proper exit codes so scheduled runs surface real failures.
4. **Decouple from module globals.** `send_data_to_db` uses bare `redis`/`db` globals bound only under `if __name__ == '__main__'` (`lectura.py`), making the functions non-importable and untestable. Pass the clients in as arguments (or build them in `main`).
5. **Resolve the in-code TODOs** (`lectura.py`): move the HTTP request after the cache check, move persistence logic into `services/`, add the local-file cache path, add explicit date/reverse fetch helpers.

## P2 — hardening
6. **Tests.** Add a unit test that runs `bs_helper.get_lecture_pieces` against `lectura.html` and asserts the 3 readings; mock Mongo/Redis for the persistence path.
7. **CI schedule vs. name.** `.github/workflows/scraper.yaml` cron `35 3 1 * 0` fires on Sundays **and** the 1st of each month (cron OR-semantics), not "Daily" as the workflow is named. Align the name with the schedule (or switch to true daily), add `workflow_dispatch` for manual runs, and remove the unused `UPSTACK_CONNECTION_STR` secret.
8. **Remove dead code.** With the fixes above, `edate`/`sdate`/`now`/`now_eu` and the commented local-file cache block in `lectura.py` are unused.
9. **Fill the LICENSE placeholder** — `Copyright [yyyy] [name of copyright owner]` is still the Apache template default.

## P3 — nice to have
10. Packaging (`pyproject.toml`) and a linter/formatter (ruff + black).
11. Pin the Docker base image by digest; cache pip in CI; add failure notifications (e.g. Slack/email) to the workflow.
