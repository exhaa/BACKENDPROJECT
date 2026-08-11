from redis_connection import redis_conn
from rq import Worker, Queue

queues = [Queue("dead_letter", connection=redis_conn)]

worker = Worker(queues, connection=redis_conn)

worker.work()