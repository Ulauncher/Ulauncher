import time
from unittest.mock import Mock

from ulauncher.utils.timer import timer

TIMER_BUFFER = 0.02  # seconds


def padded_wait(seconds: float) -> None:
    """Wait the given number of seconds plus a small buffer to ensure timer execution."""
    time.sleep(seconds + TIMER_BUFFER)


class TestTimer:
    def test_timer_executes_function(self) -> None:
        """Test that timer executes the function after the delay."""
        func = Mock()
        delay = 0.1

        ctx = timer(delay, func)

        # Function should not be called immediately
        func.assert_not_called()

        padded_wait(delay)

        func.assert_called_once()
        ctx.cancel()

    def test_timer_cancel(self) -> None:
        """Test that cancelling a timer prevents execution."""
        func = Mock()
        delay = 0.1

        ctx = timer(delay, func)

        # Cancel immediately
        ctx.cancel()

        padded_wait(delay)

        # Function should not be called
        func.assert_not_called()

    def test_timer_multiple_instances(self) -> None:
        """Test that multiple timer instances work independently."""
        func1 = Mock()
        func2 = Mock()

        ctx1 = timer(0.05, func1)
        ctx2 = timer(0.1, func2)

        # Wait for first timer
        padded_wait(0.05)
        func1.assert_called_once()
        func2.assert_not_called()

        # Wait for second timer
        padded_wait(0.05)
        func1.assert_called_once()
        func2.assert_called_once()

        # Clean up
        ctx1.cancel()
        ctx2.cancel()
