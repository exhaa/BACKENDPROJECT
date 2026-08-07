from functools import wraps
from flask import jsonify, request, make_response
import json
from redis_client import redis_client


def invalidate_cache(pattern):
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)

def cache_response(timeout=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = request.full_path

            cached = redis_client.get(cache_key)

            if cached:
                print("Serving from Redis Cache")
                return jsonify(json.loads(cached))

            response = make_response(func(*args, **kwargs))

            redis_client.set(
                cache_key,
                json.dumps(response.get_json()),
                ex=timeout
            )

            print("Saved to Redis Cache")

            return response

        return wrapper
    return decorator