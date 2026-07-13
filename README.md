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
                                   ┌──────────────────────────┴───────────────┐
                                   ▼                                           ▼
                            Redis (cache, keyed                 MongoDB (collection "readings",
                            by reading date)                    deduped by date_raw)
```

- `lectura.py` — entry point. `run_today` parses the "today" accordion; `run_tomorrow` / `run_upcoming` resolve the dated `/events/` pages and walk the next-day links forward. Each reading is written to Redis + MongoDB.
- `services/bs_helper.py` — BeautifulSoup parser handling **both** page wrappers (the accordion `div.mec-single-event-description` and the `/events/` page `div.mec-divi-content`), over an arbitrary number of `<h2>` sections. Returns `{ title, date_title, date_raw, lecturas: [ { title, content, first_line, psalm|last_line } ] }`, or `None` when the page holds no reading.
- `services/source.py` — discovers the dated `/events/` URLs from the page links (tomorrow, and the next/prev day from any event page) and extracts the `YYYY-MM-DD` embedded in an event URL.
- `services/db.py` — MongoDB client (`MongoUp`). Inserts into the `readings` collection, deduping by `date_raw`.
- `services/db_cache.py` — Redis client (`RedisUp`). Caches each reading JSON, keyed by its date.

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

Copy `.env.demo` to `.env`. The demo values target the local Docker stack; for production point them at MongoDB Atlas + Upstash.

| Variable | Purpose | Local default | Cloud |
| --- | --- | --- | --- |
| `DB_URI` | Full Mongo connection string (wins over the parts below) | `mongodb://mongo:27017` | leave empty |
| `DB_NAME` | Mongo database | `dailyreading` | `dailyreading` |
| `DB_HOST` / `DB_USERNAME` / `DB_PASSWORD` | Build an Atlas `mongodb+srv://` URI when `DB_URI` is empty | — | Atlas cluster creds |
| `UPSTACK_ENDPOINT` / `UPSTACK_PORT` | Redis host/port | `redis` / `6379` | Upstash endpoint |
| `UPSTACK_PASSWORD` | Redis password (empty = no auth) | empty | Upstash password |
| `UPSTACK_SSL` | TLS for Redis (`true` for Upstash, `false` for local) | `false` | `true` |

## Scheduled runs (production)

`.github/workflows/scraper.yaml` runs the scraper **daily** via GitHub Actions (`cron: 30 5 * * *`), reading the Mongo/Upstash credentials from repository **secrets**. It can also be triggered manually from the Actions tab (`workflow_dispatch`).

## License

Apache 2.0 — see [LICENSE](./LICENSE).
