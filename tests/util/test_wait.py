import pytest
from time import time
from ulauncher.util.wait import wait_until_true, WaitUntilTrueError


def test_wait_until_true__success():
    t_start = time()

    def callback():
        return time() - t_start > 0.05

    wait_until_true(callback, wait_sec=0.07, check_interval_sec=0.01)


def test_wait_until_true__error():
    t_start = time()

    def callback():
        return time() - t_start > 0.05

    with pytest.raises(WaitUntilTrueError):
        wait_until_true(callback, wait_sec=0.04, check_interval_sec=0.01)
