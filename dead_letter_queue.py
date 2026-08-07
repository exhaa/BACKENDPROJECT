from rq import Queue
from redis_connection import redis_conn

dead_letter_queue = Queue(
    "dead_letter",
    connection=redis_conn
)