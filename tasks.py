import time

from dead_letter_queue import dead_letter_queue
from dlq_tasks import save_failed_job

attempt = 0

def send_email_task(email):
    global attempt

    attempt += 1

    print(f"Attempt #{attempt}")

    time.sleep(2)

    try:
        if attempt < 5:
            raise Exception("SMTP Server Timeout")

        print("Email sent!")

    except Exception as e:

        if attempt >= 5:
            dead_letter_queue.enqueue(
                save_failed_job,
                {
                    "email": email,
                    "reason": str(e)
                }
            )

        raise