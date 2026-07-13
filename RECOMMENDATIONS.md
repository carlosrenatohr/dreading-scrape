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
- **CI schedule vs. name (was P2):** `.github/workflows/scraper.yaml` now runs a genuine daily cron (`30 5 * * *`) matching the "Daily Reading Scraping" name, adds `workflow_dispatch` for manual runs, and drops the unused `UPSTACK_CONNECTION_STR` secret and the dead PYTHONPATH block.
- **Structured logging + injectable clients (was P1):** `print` replaced with the `logging` module; `send_data_to_db`/`run_today`/`main` now receive the Redis and Mongo clients as arguments instead of module globals, so they are importable and testable.
- **Unit tests (was P2):** pytest suite — the parser against a synthetic MEC-accordion fixture, and `send_data_to_db` insert/dedup/skip paths with fakes; `pytest` pinned in `requirements-dev.txt`.
- **Cleanup:** removed the stray in-code TODOs and the dead commented-out cache block in `lectura.py`.

## P0 — blocks fresh data (the source site changed)
1. **Site-change caveats (the rework is done, but note the trade-offs).** The 2026 site only serves a single "today" page (`?f=YYYY-MM-DD` is ignored), so:
   - Only **today's** reading can be fetched; historical/future readings are no longer available from the source. Coverage now depends on running the job daily and accumulating.
   - `date_raw`/`date_title` are stamped from the run instant in Europe/Madrid (there is no `<time>` on the page). A run near midnight vs. Madrid time may attribute the reading to the adjacent day.
   - The parser was verified against a weekday 3-reading page; **second-reading Sundays** (a 4th `<h2>`) are handled generically but not yet verified against a live Sunday page.
   - The bundled `lectura.html` is the *old* layout only — keep it as a historical fixture, not a current parser reference.

## P1 — correctness & reliability
2. **Optional flow refactors** (`lectura.py`): move the HTTP request after the cache check (skip the fetch when the reading is already cached), and move the persistence logic into `services/`. The stray TODO comments that tracked these were removed; behavior is correct as-is.

## P2 — hardening
6. **Wire or drop the offline cache.** `get_html_local_file` is now unused (its only caller, the commented cache block, was removed). Either wire it as an offline fixture cache in `get_html_content` or delete it.
7. **Fill the LICENSE placeholder** — `Copyright [yyyy] [name of copyright owner]` is still the Apache template default.

## P3 — nice to have
10. Packaging (`pyproject.toml`) and a linter/formatter (ruff + black).
11. Pin the Docker base image by digest; cache pip in CI; add failure notifications (e.g. Slack/email) to the workflow.
