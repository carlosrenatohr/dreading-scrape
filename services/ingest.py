"""Write readings to the dreading-api-worker (Cloudflare Worker + D1) via its
token-guarded POST /api/ingest endpoint.

`IngestClient` is a drop-in for the `db_client` that lectura.send_data_to_db
expects: `get_doc` is a no-op (the Worker upserts by date_raw, so no dedup
pre-check is needed) and `post_doc` POSTs the reading. `NullCache` stands in for
the Redis client when the Worker/D1 is the datastore and no cache is used.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)


class IngestClient:
    def __init__(self, url=None, token=None):
        self._url = url or os.getenv('INGEST_URL')
        self._token = token or os.getenv('INGEST_TOKEN')

    def get_doc(self, collection_name, query):
        return None

    def post_doc(self, collection_name, doc):
        headers = {'Authorization': f'Bearer {self._token}', 'Content-Type': 'application/json'}
        response = requests.post(self._url, headers=headers, json=doc, timeout=30)
        response.raise_for_status()
        return response.json().get('date_raw')


class NullCache:
    def post(self, key, content):
        return None

    def get(self, key):
        return None
