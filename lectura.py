import logging
import requests
from services.db import MongoUp
from services.db_cache import RedisUp
import services.bs_helper as scrapper

logger = logging.getLogger(__name__)

readings_table_name = 'readings'

# The source site was restructured (2026-07): the old
# `/calendario-lecturas/evangelio-del-dia/hoy` path now 301-redirects here, the
# `?f=YYYY-MM-DD` date param is ignored, and only a single "today" page exists,
# so per-date / date-range fetching is no longer possible.
URL_TODAY = 'https://www.ciudadredonda.org/evangelio-lecturas-hoy/'
URL = URL_TODAY


def request_web_content(date=None):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    # Only a single "today" page exists now; `date` is accepted for backwards
    # compatibility but the site ignores per-date requests. Follow redirects.
    response = requests.get(URL_TODAY, headers=headers, allow_redirects=True)
    if response.status_code == 200:
        return response.text

    return None


def create_html_local_file(content):
    try:
        with open('lectura.html', 'w') as file:
            file.write(content)
    except:
        pass


def get_html_local_file():
    content = None

    try:
        with open('lectura.html', 'r') as file:
            content = file.read()
    except:
        pass

    return content


def get_html_content():
    content = request_web_content()
    create_html_local_file(content)

    return content


def run_today(redis_client, db_client):
    content = get_html_content()
    send_data_to_db(content, redis_client, db_client)


# The site no longer serves per-date or date-range readings (only a single
# "today" page, see the URL note above). These range helpers are kept so
# existing callers/imports don't break, but they now just fetch today.
def run_from_date(redis_client, db_client, start_date=None, end_date=None):
    run_today(redis_client, db_client)


def run_from_last_week(redis_client, db_client):
    run_today(redis_client, db_client)


def run_from_next_week(redis_client, db_client):
    run_today(redis_client, db_client)


def send_data_to_db(content, redis_client, db_client):
    res = scrapper.get_lecture_pieces(content)
    if not res:
        logger.info('No reading found for this date, skipping.')
        return
    # Key the cache by the reading's own date.
    cache_id = redis_client.post(res['date_raw'], res)
    logger.info('Cache id: %s', cache_id)
    # avoid duplicates in the database
    where = {'date_raw': res['date_raw']}
    inserted_id = db_client.get_doc(readings_table_name, where)
    if not inserted_id:
        inserted_id = db_client.post_doc(readings_table_name, res)
    logger.info('Mongo id: %s', inserted_id)


def main(redis_client, db_client):
    logging.basicConfig(level=logging.INFO)
    run_today(redis_client, db_client)


if __name__ == '__main__':
    main(RedisUp(), MongoUp())
