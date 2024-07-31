from datetime import datetime, timedelta
from time import sleep


def wait_until(timeout, snooze=3):
    def wait_until_decorator(api_func):
        def wrapped(*args, **kwargs):
            endtime = datetime.now() + timedelta(seconds=timeout)
            while endtime > datetime.now():
                qualified, (code, data) = api_func(*args, **kwargs)
                if qualified:
                    break
                sleep(snooze)
            return qualified, (code, data)

        return wrapped

    return wait_until_decorator
