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
- **Reworked for the 2026 site (was P0):** URLs repointed to `/evangelio-lecturas-hoy/` (redirects followed), and `services/bs_helper.py` rewritten to parse the Modern Events Calendar accordion (`div.mec-single-event-description` → `<h2>` sections → `<p>` bodies). Verified pulling a full, real reading (first reading + psalm + gospel) from the live site into local Mongo.
- **Fail loud on Mongo connect (was P1):** `MongoUp.connect` now re-raises instead of swallowing the error, so a failed run exits non-zero.

## P0 — blocks fresh data (the source site changed)
1. **Site-change caveats (the rework is done, but note the trade-offs).** The 2026 site only serves a single "today" page (`?f=YYYY-MM-DD` is ignored), so:
   - Only **today's** reading can be fetched; historical/future readings are no longer available from the source. Coverage now depends on running the job daily and accumulating.
   - `date_raw`/`date_title` are stamped from the run instant in Europe/Madrid (there is no `<time>` on the page). A run near midnight vs. Madrid time may attribute the reading to the adjacent day.
   - The parser was verified against a weekday 3-reading page; **second-reading Sundays** (a 4th `<h2>`) are handled generically but not yet verified against a live Sunday page.
   - The bundled `lectura.html` is the *old* layout only — keep it as a historical fixture, not a current parser reference.

## P1 — correctness & reliability
2. **Replace `print` with `logging`** and return/propagate proper exit codes so scheduled runs surface real failures.
4. **Decouple from module globals.** `send_data_to_db` uses bare `redis`/`db` globals bound only under `if __name__ == '__main__'` (`lectura.py`), making the functions non-importable and untestable. Pass the clients in as arguments (or build them in `main`).
5. **Resolve the in-code TODOs** (`lectura.py`): move the HTTP request after the cache check, move persistence logic into `services/`, add the local-file cache path, add explicit date/reverse fetch helpers.

## P2 — hardening
6. **Tests.** Add a unit test that runs `bs_helper.get_lecture_pieces` against `lectura.html` and asserts the 3 readings; mock Mongo/Redis for the persistence path.
7. **CI schedule vs. name.** `.github/workflows/scraper.yaml` cron `35 3 1 * 0` fires on Sundays **and** the 1st of each month (cron OR-semantics), not "Daily" as the workflow is named. Align the name with the schedule (or switch to true daily), add `workflow_dispatch` for manual runs, and remove the unused `UPSTACK_CONNECTION_STR` secret.
8. **Remove remaining dead code.** The unused module-level date globals were retired during the site rework; the commented-out local-file cache block in `lectura.py` (`get_html_content`) is still there and can be dropped or wired up as an offline cache.
9. **Fill the LICENSE placeholder** — `Copyright [yyyy] [name of copyright owner]` is still the Apache template default.

## P3 — nice to have
10. Packaging (`pyproject.toml`) and a linter/formatter (ruff + black).
11. Pin the Docker base image by digest; cache pip in CI; add failure notifications (e.g. Slack/email) to the workflow.
