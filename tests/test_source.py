import os

from services import source

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _read(name):
    with open(os.path.join(FIXTURE_DIR, name), 'r', encoding='utf-8') as fh:
        return fh.read()


def test_date_from_event_url():
    url = 'https://www.ciudadredonda.org/events/lecturas-del-xvi-domingo-del-tiempo-ordinario_2026-07-19/'
    assert source.date_from_event_url(url) == '2026-07-19'
    assert source.date_from_event_url('https://www.ciudadredonda.org/otra/') is None


def test_tomorrow_event_url_picks_the_lecturas_link():
    url = source.tomorrow_event_url(_read('manana.html'))

    assert url is not None
    assert 'lecturas-del-lunes' in url
    assert 'liturgia-viva' not in url
    assert source.date_from_event_url(url) == '2026-07-14'


def test_next_and_prev_event_urls():
    html = _read('event_nav.html')

    assert source.date_from_event_url(source.next_event_url(html)) == '2026-07-20'
    assert source.date_from_event_url(source.prev_event_url(html)) == '2026-07-18'
