import os
import json
import redis 
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
        self._redis = redis.Redis(
            host= self._endpoint,
            port= self._port,
            password= self._password,
        )

    def post(self, key, content):
        if not self._redis:
            self._connect()
        # avoid inserting the same content
        if not self._redis.get(key):
            content = json.dumps(content)
            self._redis.set(key, content)
        return self._redis.get(key)

    def get(self, key):
        return self._redis.get(key)