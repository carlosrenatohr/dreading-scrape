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
- **Dropped the unused offline-cache helpers (was P2):** removed `get_html_local_file` and `create_html_local_file` (the latter clobbered the `lectura.html` fixture on every run); `run_today` now fetches directly.
- **Filled the Apache LICENSE copyright** (was P2).
- **Test CI:** `.github/workflows/tests.yaml` runs the pytest suite on every push and pull request (no external services needed — the tests use a fixture and fakes).
- **Dated fetching restored + Sunday support (was P0):** the parser now also reads the `/events/…_DATE/` pages (`div.mec-divi-content`), so Sundays and feasts with a **Segunda Lectura** parse (verified live: 4 sections). `services/source.py` discovers the dated event URLs (tomorrow, and the next/prev day from any event page) and `run_upcoming` walks them forward, persisting each reading under the date embedded in its URL — verified live pulling 2026-07-14…07-20 into Mongo. The bundled `lectura.html` is the *old* layout, kept as a historical fixture only.

## P1 — correctness & reliability
1. **Remaining source trade-offs.** Historical backfill isn't available — the site is forward-looking, so coverage accumulates going forward from the daily run. The "today" accordion page has no date marker so it is stamped from the run in Europe/Madrid (a run near midnight may attribute it to the adjacent day); the dated `/events/` pages are exact (date from the URL).
2. **Optional flow refactors** (`lectura.py`): move the HTTP request after the cache check (skip the fetch when the reading is already cached), and move the persistence logic into `services/`. The stray TODO comments that tracked these were removed; behavior is correct as-is.

## P2 — hardening
6. **Fill the LICENSE placeholder** — `Copyright [yyyy] [name of copyright owner]` is still the Apache template default.

## P3 — nice to have
10. Packaging (`pyproject.toml`) and a linter/formatter (ruff + black).
11. Pin the Docker base image by digest; cache pip in CI; add failure notifications (e.g. Slack/email) to the workflow.
