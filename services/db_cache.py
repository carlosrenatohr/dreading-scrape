import os
import json
import redis
from redis.connection import ConnectionPool, SSLConnection
from dotenv import load_dotenv

load_dotenv()


def _is_truthy(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


class RedisUp:
    def __init__(self):
        self._endpoint = os.getenv('UPSTACK_ENDPOINT')
        self._port = os.getenv('UPSTACK_PORT')
        # Empty password means an unauthenticated local Redis; keep it None.
        self._password = os.getenv('UPSTACK_PASSWORD') or None
        # Upstash requires TLS; plain local Redis does not. Toggle via UPSTACK_SSL.
        self._ssl = _is_truthy(os.getenv('UPSTACK_SSL', 'true'))
        self._redis = None
        self._connect()

    def _connect(self):
        pool = ConnectionPool(
            host=self._endpoint,
            port=self._port,
            password=self._password,
            connection_class=SSLConnection if self._ssl else redis.Connection,
        )
        self._redis = redis.Redis(connection_pool=pool)

    def post(self, key, content):
        if not self._redis:
            self._connect()
        cache_id = self._redis.get(key)
        # avoid inserting the same content
        if not cache_id:
            self._redis.set(key, json.dumps(content))
        return cache_id

    def get(self, key):
        return self._redis.get(key)