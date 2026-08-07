from redis_client import redis_client
import time

# Store a key for 30 seconds
redis_client.set("session", "abc123", ex=30)

print("Value:", redis_client.get("session"))
print("TTL:", redis_client.ttl("session"))

time.sleep(31)

print("After Expiry:", redis_client.get("session"))