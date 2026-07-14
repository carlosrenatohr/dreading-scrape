import logging
import os

import requests

from services.db import MongoUp
from services.db_cache import RedisUp
from services.ingest import IngestClient, NullCache
from services import source
from services import enrich
import services.bs_helper as scrapper

logger = logging.getLogger(__name__)

readings_table_name = 'readings'

BASE = 'https://www.ciudadredonda.org'
# "Today" is the Modern Events Calendar accordion page (no date marker of its
# own). "Tomorrow" is a teaser that links to a dated /events/ page; from there
# the next/prev links (see services.source) let us walk the calendar forward.
URL_TODAY = f'{BASE}/evangelio-lecturas-hoy/'
URL_TOMORROW = f'{BASE}/evangelio-de-manana/'

_HEADERS = {'User-Agent': 'Mozilla/5.0'}


def request_web_content(url=URL_TODAY):
    # Fetch a page, following redirects; return its HTML on 200, else None.
    response = requests.get(url, headers=_HEADERS, allow_redirects=True)
    if response.status_code == 200:
        return response.text
    logger.warning('Fetch failed (%s) for %s', response.status_code, url)
    return None


def _date_raw_from(url):
    date = source.date_from_event_url(url)
    return f'{date}T00:00:00Z' if date else None


def send_data_to_db(content, redis_client, db_client, date_raw=None):
    # date_raw, when known from the source URL (the /events/ pages embed it),
    # gives the reading its real date; otherwise the parser stamps today (used
    # for the "today" accordion page, which carries no date).
    res = scrapper.get_lecture_pieces(content, date_raw)
    if not res:
        logger.info('No reading found, skipping.')
        return
    # Add the supplementary reflection / kids version / message / image prompt.
    res = enrich.enrich(res)
    # Key the cache by the reading's own date.
    cache_id = redis_client.post(res['date_raw'], res)
    logger.info('Cache id: %s', cache_id)
    # avoid duplicates in the database
    where = {'date_raw': res['date_raw']}
    inserted_id = db_client.get_doc(readings_table_name, where)
    if not inserted_id:
        inserted_id = db_client.post_doc(readings_table_name, res)
    logger.info('Mongo id: %s', inserted_id)


def run_today(redis_client, db_client):
    send_data_to_db(request_web_content(URL_TODAY), redis_client, db_client)


def _run_event(url, redis_client, db_client):
    # Fetch one dated /events/ page and persist it under the date in its URL.
    content = request_web_content(url)
    if content:
        send_data_to_db(content, redis_client, db_client, _date_raw_from(url))
    return content


def run_tomorrow(redis_client, db_client):
    teaser = request_web_content(URL_TOMORROW)
    url = source.tomorrow_event_url(teaser) if teaser else None
    if not url:
        logger.warning('No tomorrow reading link found on %s', URL_TOMORROW)
        return
    _run_event(url, redis_client, db_client)


def run_upcoming(redis_client, db_client, days=7):
    # Anchor at tomorrow's event page and walk the "next day" links forward,
    # persisting each dated reading (deduped by date). Stops after `days` pages
    # or when the next-day chain ends.
    teaser = request_web_content(URL_TOMORROW)
    url = source.tomorrow_event_url(teaser) if teaser else None
    fetched = 0
    while url and fetched < days:
        content = _run_event(url, redis_client, db_client)
        url = source.next_event_url(content) if content else None
        fetched += 1


def main(redis_client, db_client):
    logging.basicConfig(level=logging.INFO)
    run_today(redis_client, db_client)
    run_upcoming(redis_client, db_client, days=7)


def build_clients():
    # Write to the D1 Worker via /api/ingest when INGEST_URL is set; otherwise
    # use the classic Redis (Upstash) + MongoDB path.
    if os.getenv('INGEST_URL'):
        return NullCache(), IngestClient()
    return RedisUp(), MongoUp()


if __name__ == '__main__':
    main(*build_clients())
