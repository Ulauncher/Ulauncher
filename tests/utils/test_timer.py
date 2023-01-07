from unittest import mock
import pytest
from ulauncher.utils.timer import timer


class TestTimer:
    @pytest.fixture(autouse=True)
    def GLib(self, mocker):
        return mocker.patch("ulauncher.utils.timer.GLib")

    def test_timer_subsecond(self, GLib):
        func = mock.Mock()
        subsecond_time = 0.5
        ctx = timer(subsecond_time, func)
        GLib.timeout_source_new.assert_called_with(subsecond_time * 1000)
        src = ctx.source
        ctx.trigger(None)
        func.assert_called_once()
        ctx.cancel()
        src.destroy.assert_called_once()

    def test_timer_second(self, GLib):
        func = mock.Mock()
        seconds_time = 2
        ctx = timer(seconds_time, func)
        GLib.timeout_source_new_seconds.assert_called_with(seconds_time)
        src = ctx.source
        ctx.trigger(None)
        func.assert_called_once()
        ctx.cancel()
        src.destroy.assert_called_once()
