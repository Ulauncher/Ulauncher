from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture

from ulauncher.utils.timer import timer


class TestTimer:
    @pytest.fixture(autouse=True)
    def glib(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.utils.timer.GLib")

    def test_timer_subsecond(self, glib: MagicMock) -> None:
        func = Mock()
        subsecond_time = 0.5
        ctx = timer(subsecond_time, func)
        glib.timeout_source_new.assert_called_with(subsecond_time * 1000)
        src: Any = ctx.source
        ctx.trigger(None)
        func.assert_called_once()
        ctx.cancel()
        src.destroy.assert_called_once()

    def test_timer_second(self, glib: MagicMock) -> None:
        func = Mock()
        seconds_time = 2
        ctx = timer(seconds_time, func)
        glib.timeout_source_new_seconds.assert_called_with(seconds_time)
        src: Any = ctx.source
        ctx.trigger(None)
        func.assert_called_once()
        ctx.cancel()
        src.destroy.assert_called_once()
