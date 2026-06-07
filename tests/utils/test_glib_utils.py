from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture

from ulauncher.utils.glib_utils import SchedulerContext, run_when_idle, timer


@pytest.fixture(autouse=True)
def glib(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("ulauncher.utils.glib_utils.GLib")


class TestSchedulerContext:
    def test_cancel_idempotent(self, glib: MagicMock) -> None:
        ctx = SchedulerContext(42)
        ctx.cancel()
        ctx.cancel()
        glib.source_remove.assert_called_once_with(42)
        assert ctx.source_id is None


class TestTimer:
    def test_timer_schedules_callback_with_delay_in_milliseconds(self, glib: MagicMock) -> None:
        timer(0.1, Mock())
        assert glib.timeout_add.call_args[0][0] == 100

    def test_timer_returns_a_scheduler_context(self, glib: MagicMock) -> None:
        glib.timeout_add.return_value = 42
        ctx = timer(0.1, Mock())
        ctx.cancel()
        glib.source_remove.assert_called_once_with(42)

    def test_timer_callback_runs_func_once_and_signals_removal(self, glib: MagicMock) -> None:
        func = Mock()
        timer(0.1, func)
        callback = glib.timeout_add.call_args[0][1]
        assert callback() is False
        func.assert_called_once()

    def test_timer_forwards_positional_and_keyword_arguments(self, glib: MagicMock) -> None:
        func = Mock()
        timer(0.1, func, "arg1", "arg2", kw="value")
        callback = glib.timeout_add.call_args[0][1]
        assert callback() is False
        func.assert_called_once_with("arg1", "arg2", kw="value")


class TestRunWhenIdle:
    def test_run_when_idle_returns_a_scheduler_context(self, glib: MagicMock) -> None:
        glib.idle_add.return_value = 67
        ctx = run_when_idle(Mock())
        ctx.cancel()
        glib.source_remove.assert_called_once_with(67)

    def test_run_when_idle_callback_runs_func_once_and_signals_removal(self, glib: MagicMock) -> None:
        func = Mock()
        run_when_idle(func)
        callback = glib.idle_add.call_args[0][0]
        assert callback() is False
        func.assert_called_once()

    def test_run_when_idle_forwards_positional_and_keyword_arguments(self, glib: MagicMock) -> None:
        func = Mock()
        run_when_idle(func, "arg1", "arg2", kw="value")
        callback = glib.idle_add.call_args[0][0]
        assert callback() is False
        func.assert_called_once_with("arg1", "arg2", kw="value")
