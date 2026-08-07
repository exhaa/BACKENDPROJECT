from redis_client import redis_client
import time


def test_redis_expiry():
    redis_client.set("session", "abc123", ex=2)

    assert redis_client.get("session") == "abc123"

    time.sleep(3)

    assert redis_client.get("session") is None