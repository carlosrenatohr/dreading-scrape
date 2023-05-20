import os
import json
import redis 
from dotenv import load_dotenv

load_dotenv()

DB_ENDPOINT = os.getenv("UPSTACK_ENDPOINT")
DB_PORT = os.getenv("UPSTACK_PORT")
DB_PASSWORD = os.getenv("UPSTACK_PASSWORD")

def connect():
  r = redis.Redis(
    host= DB_ENDPOINT,
    port= DB_PORT,
    password=DB_PASSWORD,
  )
  
  return r

def post(key, content):
    r = connect()
    content = json.dumps(content)
    r.set(key, content)
    print(r.get(key))