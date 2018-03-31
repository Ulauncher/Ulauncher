from time import time, sleep


def wait_until_true(callback, wait_sec=10, check_interval_sec=0.1):
    t_start = time()
    while not callback():
        if time() - t_start > wait_sec:
            raise WaitUntilTrueError()
        sleep(check_interval_sec)


class WaitUntilTrueError(Exception):
    pass
