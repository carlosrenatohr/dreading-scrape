# dreading-scrape

Scraper for the Catholic **daily liturgical readings** ("evangelio y lecturas del día"). It fetches the reading page from [ciudadredonda.org](https://www.ciudadredonda.org), parses the title, date and each reading (first reading, psalm, gospel), caches the result in Redis and persists it to MongoDB. It is the data producer for the companion [`dreading-api`](../dreading-api) project.

> **Status — side project, being revived.** The scraping pipeline, caching and persistence are functional and run end-to-end against a local Docker stack (see below). **The live source site was restructured after this scraper was written**, so the fetch/parse selectors need a rework before it can pull fresh data again — see [RECOMMENDATIONS.md](./RECOMMENDATIONS.md) (P0). The bundled `lectura.html` is a real page from the old layout used as a parsing fixture.

## How it works

```
ciudadredonda.org ──HTTP──▶ lectura.py ──parse──▶ bs_helper.get_lecture_pieces()
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                              ▼
             Redis (cache, keyed          MongoDB (collection
             by reading date)             "readings", deduped
                                          by date_raw)
```

- `lectura.py` — entry point. Fetches a page (today, or a date range: last/next week), then hands the HTML to the parser and writes the result to Redis + MongoDB.
- `services/bs_helper.py` — BeautifulSoup parser. Returns `{ title, date_title, date_raw, lecturas: [ { title, content, first_line, psalm|last_line } ] }`, or `None` when the page holds no reading.
- `services/db.py` — MongoDB client (`MongoUp`). Inserts into the `readings` collection, deduping by `date_raw`.
- `services/db_cache.py` — Redis client (`RedisUp`). Caches each reading JSON, keyed by its date.

Each stored reading looks like:

```json
{
  "title": "Lecturas de hoy Martes de la 6ª semana de Pascua",
  "date_title": "16 de mayo de 2023",
  "date_raw": "2023-05-16 00:00:00",
  "lecturas": [
    { "title": "Primera lectura", "content": "...", "first_line": "...", "last_line": "..." },
    { "title": "Salmo", "content": "...", "first_line": "...", "psalm": "..." },
    { "title": "Evangelio de hoy", "content": "...", "first_line": "...", "last_line": "..." }
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

`.github/workflows/scraper.yaml` runs the scraper on a cron via GitHub Actions, reading the same variables from repository **secrets**. See [RECOMMENDATIONS.md](./RECOMMENDATIONS.md) for a note on the cron expression vs. the "Daily" workflow name.

## License

Apache 2.0 — see [LICENSE](./LICENSE).
