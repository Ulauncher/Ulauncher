from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture

from ulauncher.utils import scheduling


@pytest.fixture(autouse=True)
def glib(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("ulauncher.utils.scheduling.GLib")


class TestContext:
    def test_attaches_source_with_callback(self) -> None:
        source = Mock()
        schedule = scheduling.Context(source, Mock(), repeat=False, args=(), kwargs={})
        source.set_callback.assert_called_once_with(schedule._trigger)
        source.attach.assert_called_once_with(None)

    def test_cancel_destroys_source_and_is_idempotent(self) -> None:
        source = Mock()
        schedule = scheduling.Context(source, Mock(), repeat=False, args=(), kwargs={})
        schedule.cancel()
        schedule.cancel()
        source.destroy.assert_called_once_with()
        assert schedule.source is None

    def test_trigger_runs_func_and_signals_removal_for_one_shot(self) -> None:
        func = Mock()
        schedule = scheduling.Context(Mock(), func, repeat=False, args=("a", "b"), kwargs={"kw": "v"})
        assert schedule._trigger() is False
        func.assert_called_once_with("a", "b", kw="v")

    def test_trigger_clears_source_after_one_shot_fires(self) -> None:
        schedule = scheduling.Context(Mock(), Mock(), repeat=False, args=(), kwargs={})
        schedule._trigger()
        assert schedule.source is None

    def test_trigger_signals_continuation_when_repeating(self) -> None:
        func = Mock()
        schedule = scheduling.Context(Mock(), func, repeat=True, args=(), kwargs={})
        assert schedule._trigger() is True
        func.assert_called_once_with()

    def test_trigger_signals_removal_when_func_cancels_a_repeating_schedule(self) -> None:
        schedule = scheduling.Context(Mock(), Mock(), repeat=True, args=(), kwargs={})
        schedule._func = schedule.cancel
        assert schedule._trigger() is False
        assert schedule.source is None

    def test_trigger_does_not_run_func_after_cancel(self) -> None:
        func = Mock()
        schedule = scheduling.Context(Mock(), func, repeat=True, args=(), kwargs={})
        schedule.cancel()
        assert schedule._trigger() is False
        func.assert_not_called()


class TestTimer:
    def test_creates_timeout_source_with_delay_in_milliseconds(self, glib: MagicMock) -> None:
        scheduling.timer(0.1, Mock())
        glib.timeout_source_new.assert_called_once_with(100)

    def test_returns_a_schedule(self) -> None:
        assert isinstance(scheduling.timer(0.1, Mock()), scheduling.Context)

    def test_forwards_arguments_to_func(self) -> None:
        func = Mock()
        schedule = scheduling.timer(0.1, func, "arg1", "arg2", kw="value")
        schedule._trigger()
        func.assert_called_once_with("arg1", "arg2", kw="value")


class TestRunWhenIdle:
    def test_creates_idle_source(self, glib: MagicMock) -> None:
        scheduling.run_when_idle(Mock())
        glib.idle_source_new.assert_called_once_with()

    def test_returns_a_schedule(self) -> None:
        assert isinstance(scheduling.run_when_idle(Mock()), scheduling.Context)

    def test_forwards_arguments_to_func(self) -> None:
        func = Mock()
        schedule = scheduling.run_when_idle(func, "arg1", "arg2", kw="value")
        schedule._trigger()
        func.assert_called_once_with("arg1", "arg2", kw="value")
