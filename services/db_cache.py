import os
import json
import redis 
from redis.connection import ConnectionPool
from dotenv import load_dotenv

load_dotenv()

class RedisUp:
    def __init__(self):
        self._endpoint = os.getenv('UPSTACK_ENDPOINT')
        self._port = os.getenv('UPSTACK_PORT')
        self._password = os.getenv('UPSTACK_PASSWORD')
        self._redis = None
        self._connect()

    def _connect(self):
        pool = ConnectionPool(
            host= self._endpoint,
            port= self._port,
            password= self._password,
        )
        self._redis = redis.Redis(connection_pool=pool)

    def post(self, key, content):
        cache_id = self._redis.get(key)
        if not self._redis:
            self._connect()
        # avoid inserting the same content
        if not cache_id:
            content = json.dumps(content)
            self._redis.set(key, content)
        return cache_id

    def get(self, key):
        return self._redis.get(key)