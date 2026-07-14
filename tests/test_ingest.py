from unittest.mock import MagicMock, patch

from services.ingest import IngestClient, NullCache


def test_get_doc_is_a_noop():
    assert IngestClient('http://x/api/ingest', 't').get_doc('readings', {'date_raw': 'd'}) is None


def test_post_doc_posts_with_bearer_and_returns_date():
    client = IngestClient('http://x/api/ingest', 'tok')
    resp = MagicMock()
    resp.json.return_value = {'ok': True, 'date_raw': '2026-07-19T00:00:00Z'}
    resp.raise_for_status.return_value = None

    with patch('services.ingest.requests.post', return_value=resp) as post:
        out = client.post_doc('readings', {'date_raw': '2026-07-19T00:00:00Z', 'title': 'T'})

    assert out == '2026-07-19T00:00:00Z'
    args, kwargs = post.call_args
    assert args[0] == 'http://x/api/ingest'
    assert kwargs['headers']['Authorization'] == 'Bearer tok'
    assert kwargs['json']['title'] == 'T'


def test_null_cache_is_a_noop():
    cache = NullCache()
    assert cache.post('k', 'v') is None
    assert cache.get('k') is None
