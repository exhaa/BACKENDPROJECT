from rq import Worker, Queue
from redis_connection import redis_conn
import tasks

print(tasks.__file__)

queue = Queue("default", connection=redis_conn)

worker = Worker([queue], connection=redis_conn)
worker.work()