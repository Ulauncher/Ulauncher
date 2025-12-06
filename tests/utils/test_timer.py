from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture

from ulauncher.utils.timer import timer


class TestTimer:
    @pytest.fixture(autouse=True)
    def glib(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.utils.timer.GLib")

    def test_timer(self, glib: MagicMock) -> None:
        func = Mock()
        time = 0.1
        ctx = timer(time, func)
        glib.timeout_source_new.assert_called_with(time * 1000)
        src: Any = ctx.source
        ctx.trigger(None)
        func.assert_called_once()
        ctx.cancel()
        src.destroy.assert_called_once()
