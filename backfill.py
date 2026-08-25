# Backfill missing readings by walking the calendar *backwards* from
# tomorrow's dated event page using the `pskip` (previous-day) links.
#
# Usage:
#   INGEST_URL=https://<worker>.workers.dev/api/ingest \
#   INGEST_TOKEN=<token> \
#   python backfill.py --until 2026-08-13 [--days 30]

import argparse
import logging

from lectura import _run_event, request_web_content, URL_TOMORROW, build_clients
from services import source

logger = logging.getLogger(__name__)


def backfill(clients, until_date, max_days=60):
    redis_client, db_client = clients
    teaser = request_web_content(URL_TOMORROW)
    url = source.tomorrow_event_url(teaser) if teaser else None
    if not url:
        logger.warning('No anchor event found on %s', URL_TOMORROW)
        return

    fetched = 0
    while url and fetched < max_days:
        date = source.date_from_event_url(url)
        if date and date < until_date:
            logger.info('Reached %s (< %s), done.', date, until_date)
            return
        content = _run_event(url, redis_client, db_client)
        url = source.prev_event_url(content) if content else None
        fetched += 1
    logger.info('Stopped after %d pages.', fetched)


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='Backfill past readings.')
    parser.add_argument('--until', required=True,
                        help='Inclusive start date YYYY-MM-DD to backfill from.')
    parser.add_argument('--days', type=int, default=60,
                        help='Safety cap on pages fetched.')
    args = parser.parse_args()
    backfill(build_clients(), args.until, args.days)


if __name__ == '__main__':
    main()
