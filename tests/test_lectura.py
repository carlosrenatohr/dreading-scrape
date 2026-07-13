import os
from unittest.mock import MagicMock

import lectura

FIXTURE = os.path.join(os.path.dirname(__file__), 'fixtures', 'reading_mec.html')


def _fixture_content():
    with open(FIXTURE, 'r', encoding='utf-8') as fh:
        return fh.read()


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
