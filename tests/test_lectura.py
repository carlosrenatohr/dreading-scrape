import os
from unittest.mock import MagicMock, patch

import lectura

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _read(name):
    with open(os.path.join(FIXTURE_DIR, name), 'r', encoding='utf-8') as fh:
        return fh.read()


def _fixture_content():
    return _read('reading_mec.html')


def _fake_fetch(mapping):
    # Map a URL substring to fixture HTML, mimicking request_web_content(url).
    def _fetch(url=lectura.URL_TODAY):
        for needle, html in mapping.items():
            if needle in url:
                return html
        return None
    return _fetch


def test_insert_path_when_not_duplicated():
    redis_client = MagicMock()
    db_client = MagicMock()
    db_client.get_doc.return_value = None

    lectura.send_data_to_db(_fixture_content(), redis_client, db_client)

    assert db_client.post_doc.call_count == 1
    collection, doc = db_client.post_doc.call_args.args
    assert collection == 'readings'
    assert doc['date_raw'] == redis_client.post.call_args.args[0]


def test_dedup_path_when_already_present():
    redis_client = MagicMock()
    db_client = MagicMock()
    db_client.get_doc.return_value = 'existing-mongo-id'

    lectura.send_data_to_db(_fixture_content(), redis_client, db_client)

    db_client.post_doc.assert_not_called()


def test_skip_path_when_no_reading():
    redis_client = MagicMock()
    db_client = MagicMock()

    lectura.send_data_to_db('', redis_client, db_client)

    redis_client.post.assert_not_called()
    db_client.post_doc.assert_not_called()


def test_run_tomorrow_persists_the_dated_reading():
    fetch = _fake_fetch({
        'evangelio-de-manana': _read('manana.html'),
        '_2026-07-14': _read('event_sunday.html'),
    })
    redis_client = MagicMock()
    db_client = MagicMock()
    db_client.get_doc.return_value = None

    with patch.object(lectura, 'request_web_content', side_effect=fetch):
        lectura.run_tomorrow(redis_client, db_client)

    assert db_client.post_doc.call_count == 1
    _collection, doc = db_client.post_doc.call_args.args
    assert doc['date_raw'] == '2026-07-14T00:00:00Z'


def test_run_upcoming_walks_next_links():
    fetch = _fake_fetch({
        'evangelio-de-manana': _read('manana.html'),   # -> 2026-07-14 event
        '_2026-07-14': _read('event_with_next.html'),   # -> next 2026-07-15
        '_2026-07-15': _read('event_sunday.html'),      # no next link
    })
    redis_client = MagicMock()
    db_client = MagicMock()
    db_client.get_doc.return_value = None

    with patch.object(lectura, 'request_web_content', side_effect=fetch):
        lectura.run_upcoming(redis_client, db_client, days=5)

    dates = sorted(doc['date_raw'] for _collection, doc
                   in (call.args for call in db_client.post_doc.call_args_list))
    assert dates == ['2026-07-14T00:00:00Z', '2026-07-15T00:00:00Z']
