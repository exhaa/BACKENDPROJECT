from rq import Queue
from redis_connection import redis_conn

queue = Queue(
    "default",
    connection=redis_conn
)