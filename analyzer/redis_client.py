import redis
import json
#import hashlib

r = redis.Redis(host="redis", port=6379, decode_responses=True)

def find_in_cache(key: str):
    cached = r.get(key)
    if cached:
        return json.loads(cached)
    return None

def store_in_cache(key: str, data: dict):
    r.set(key, json.dumps(data))