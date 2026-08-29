# dreading-scrape

Scraper for the Catholic **daily liturgical readings** ("evangelio y lecturas del día"). It fetches the reading page from [ciudadredonda.org](https://www.ciudadredonda.org), parses the title, date and each reading (first reading, psalm, gospel), caches the result in Redis and persists it to MongoDB. It is the data producer for the companion [`dreading-api`](../dreading-api) project.

> **Status — side project, being revived.** The scraper works end-to-end against the current (2026) `ciudadredonda.org` layout and a local Docker stack (see below). It fetches **today's** accordion page plus the **upcoming week** of dated `/events/` pages — walking the site's next-day links — parses each reading (including the **Segunda Lectura** that Sundays and feasts carry), and writes them to Redis + MongoDB. The old `?f=YYYY-MM-DD` param is gone, but the dated `/events/` pages restore per-date coverage going forward (historical backfill isn't available — the site is forward-looking). The bundled `lectura.html` is the old layout, kept as a historical fixture. See [RECOMMENDATIONS.md](./RECOMMENDATIONS.md) for the remaining backlog.

## How it works

```
 /evangelio-lecturas-hoy/  (today, accordion)  ─┐
 /evangelio-de-manana/ ─▶ /events/…_DATE/ ──────┤ HTTP   lectura.py
   walk next-day links → upcoming week           ├──────▶ (run_today / run_upcoming)
                                                  ┘            │  parse
                                         bs_helper.get_lecture_pieces()
                                                               │
                                                      enrich.enrich()
                                                               │
                                          ┌────────────────────┴────────────────────┐
                                          ▼                                          ▼
                                   INGEST_URL set?                            INGEST_URL empty?
                                          │                                          │
                              POST /api/ingest                            ┌────────┴────────┐
                              to Cloudflare Worker                        ▼                  ▼
                              (D1 + AI enrichment)                   Redis (cache)    MongoDB (persist)
```

- `lectura.py` — entry point. `run_today` parses the "today" accordion; `run_tomorrow` / `run_upcoming` resolve the dated `/events/` pages and walk the next-day links forward. When `INGEST_URL` is set (production), each reading is POSTed to the Worker's `/api/ingest` endpoint where it gets AI-enriched and stored in D1. When `INGEST_URL` is empty (local dev), readings go to Redis + MongoDB.
- `services/bs_helper.py` — BeautifulSoup parser handling **both** page wrappers (the accordion `div.mec-single-event-description` and the `/events/` page `div.mec-divi-content`), over an arbitrary number of `<h2>` sections. Returns `{ title, date_title, date_raw, lecturas: [ { title, content, first_line, psalm|last_line } ] }`, or `None` when the page holds no reading.
- `services/source.py` — discovers the dated `/events/` URLs from the page links (tomorrow, and the next/prev day from any event page) and extracts the `YYYY-MM-DD` embedded in an event URL.
- `services/ingest.py` — `IngestClient` posts readings to the Worker via `POST /api/ingest`. Used when `INGEST_URL` is set.
- `services/db.py` — MongoDB client (`MongoUp`). Legacy path only.
- `services/db_cache.py` — Redis client (`RedisUp`). Legacy path only.

Each stored reading looks like:

```json
{
  "title": "Evangelio y Lecturas del Lunes de la XV Semana del Tiempo Ordinario",
  "date_title": "13 de julio de 2026",
  "date_raw": "2026-07-13 00:00:00",
  "lecturas": [
    { "title": "Primera Lectura", "content": "...", "first_line": "...", "last_line": "Palabra de Dios" },
    { "title": "Salmo", "content": "...", "first_line": "...", "psalm": "..." },
    { "title": "Evangelio", "content": "...", "first_line": "...", "last_line": "Palabra del Señor" }
  ]
}
```

## Stack

- Python 3.11
- `requests` (HTTP), `beautifulsoup4` (parsing), `pymongo` (MongoDB), `redis` (cache), `python-dotenv` (config)
- Docker + Docker Compose for the local stack (MongoDB + Redis)

## Quickstart (local, Docker — no cloud accounts needed)

```bash
cp .env.demo .env                 # local defaults point at the bundled mongo + redis
docker compose up -d mongo redis  # start the datastores
docker compose run --rm scraper   # fetch → parse → cache → persist, then exit
```

> **Note:** The Docker setup uses the legacy MongoDB/Redis path. For the production Worker path, set `INGEST_URL` and `INGEST_TOKEN` in your `.env` and run without Docker.

Inspect what was stored:

```bash
docker compose exec mongo mongosh --quiet \
  --eval 'db.getSiblingDB("dailyreading").readings.find().limit(1).pretty()'
```

Tear down (drops the local data volume):

```bash
docker compose down -v
```

## Running without Docker

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.demo .env      # then edit for your own Mongo/Redis
python lectura.py      # run from the repo root so `services` imports resolve
```

## Configuration

Copy `.env.demo` to `.env`. For production, set `INGEST_URL` and `INGEST_TOKEN` to post directly to the Cloudflare Worker (recommended). When `INGEST_URL` is empty, the scraper falls back to the legacy MongoDB + Redis path.

| Variable | Purpose | Default |
| --- | --- | --- |
| `INGEST_URL` | Worker `/api/ingest` endpoint — enables Worker path | empty (legacy) |
| `INGEST_TOKEN` | Bearer token for `/api/ingest` | empty (set via secrets) |
| `DB_URI` | Full Mongo connection string (legacy) | `mongodb://mongo:27017` |
| `DB_NAME` | Mongo database (legacy) | `dailyreading` |
| `UPSTACK_ENDPOINT` / `UPSTACK_PORT` | Redis host/port (legacy) | `redis` / `6379` |

## Scheduled runs (production)

`.github/workflows/scraper.yml` runs the scraper **daily** at 05:30 UTC via GitHub Actions cron. It reads `INGEST_TOKEN` from repository secrets. It can also be triggered manually from the Actions tab (`workflow_dispatch`).

## Manual triggers

| What | Command / Action | When to use |
| --- | --- | --- |
| **Re-scrape today** | Actions tab → "Scraper — daily ingest" → Run workflow | After a bad scrape, or to regenerate today's reading with AI enrichment + image |
| **Re-scrape specific date** | `INGEST_URL=... INGEST_TOKEN=... python -m lectura` locally | Debugging a specific date |
| **Deploy Worker** | Push to `main` on `dreading-api-worker` (auto) or `pnpm run deploy` | After code changes to the Worker |

> **Important:** The Worker only enriches readings (AI reflection + image) when they arrive via `/api/ingest`. Existing readings in D1 are **not** re-enriched. To regenerate an image for a past date, re-scrape that day's reading.

## License

Apache 2.0 — see [LICENSE](./LICENSE).
