from __future__ import annotations

from typing import Callable
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.internals import effects, result_buffer
from ulauncher.internals.result import Result
from ulauncher.internals.result_buffer import ResultBuffer


class TestResultBuffer:
    @pytest.fixture
    def buffer(self) -> ResultBuffer:
        return ResultBuffer()

    @pytest.fixture
    def emit(self) -> MagicMock:
        """Spy receiving (results, append) for each paint the buffer flushes."""
        return MagicMock()

    @pytest.fixture
    def captured_flush(self, mocker: MockerFixture) -> list[Callable[[], None]]:
        """Capture the throttle's scheduled flush instead of arming a real timer."""
        captured: list[Callable[[], None]] = []
        mocker.patch.object(
            result_buffer.scheduling, "timer", side_effect=lambda _delay, func: (captured.append(func), MagicMock())[1]
        )
        return captured

    def test_replace_final_renders_immediately(self, buffer: ResultBuffer, emit: MagicMock) -> None:
        r = Result(name="a")
        buffer.enqueue(effects.render_results([r], append=False, final=True), emit)
        emit.assert_called_once_with([r], False)

    def test_append_first_is_forced_to_replace(self, buffer: ResultBuffer, emit: MagicMock) -> None:
        r = Result(name="a")
        buffer.enqueue(effects.render_results([r], append=True, final=True), emit)
        emit.assert_called_once_with([r], False)

    def test_append_after_first_paint_appends(
        self, buffer: ResultBuffer, emit: MagicMock, captured_flush: list[Callable[[], None]]
    ) -> None:
        first, second = Result(name="a"), Result(name="b")
        buffer.enqueue(effects.render_results([first], append=False, final=False), emit)  # schedules a flush
        captured_flush[0]()  # first paint
        buffer.enqueue(effects.render_results([second], append=True, final=True), emit)
        assert emit.call_args_list[0].args == ([first], False)
        assert emit.call_args_list[1].args == ([second], True)

    def test_replace_after_append_replaces(self, buffer: ResultBuffer, emit: MagicMock) -> None:
        a, b, c = Result(name="a"), Result(name="b"), Result(name="c")
        buffer.enqueue(effects.render_results([a], append=False, final=True), emit)  # first paint
        buffer.enqueue(effects.render_results([b], append=True, final=True), emit)  # appends onto it
        buffer.enqueue(effects.render_results([c], append=False, final=True), emit)  # replace must not leak a, b
        assert emit.call_args_list[-1].args == ([c], False)

    def test_replace_drafts_coalesce_to_latest(
        self, buffer: ResultBuffer, emit: MagicMock, captured_flush: list[Callable[[], None]]
    ) -> None:
        base, draft2, draft3 = Result(name="base"), Result(name="2"), Result(name="3")
        buffer.enqueue(effects.render_results([base], append=False, final=False), emit)  # schedules a flush
        buffer.enqueue(effects.render_results([draft2], append=False, final=False), emit)  # coalesced into pending
        buffer.enqueue(effects.render_results([draft3], append=False, final=False), emit)  # coalesced into pending
        assert len(captured_flush) == 1
        captured_flush[0]()
        assert emit.call_args_list[-1].args == ([draft3], False)

    def test_appends_batch_within_window(
        self, buffer: ResultBuffer, emit: MagicMock, captured_flush: list[Callable[[], None]]
    ) -> None:
        base, a, b = Result(name="base"), Result(name="a"), Result(name="b")
        buffer.enqueue(effects.render_results([base], append=False, final=False), emit)  # schedules a flush
        captured_flush[0]()  # first paint
        buffer.enqueue(effects.render_results([a], append=True, final=False), emit)  # schedules a flush
        buffer.enqueue(effects.render_results([b], append=True, final=False), emit)  # batched into pending
        captured_flush[1]()
        assert emit.call_args_list[-1].args == ([a, b], True)

    def test_append_onto_pending_replace_stays_replace(
        self, buffer: ResultBuffer, emit: MagicMock, captured_flush: list[Callable[[], None]]
    ) -> None:
        base, draft, extra = Result(name="base"), Result(name="draft"), Result(name="extra")
        buffer.enqueue(effects.render_results([base], append=False, final=False), emit)  # schedules a flush
        buffer.enqueue(effects.render_results([draft], append=False, final=False), emit)  # un-flushed replace
        buffer.enqueue(effects.render_results([extra], append=True, final=False), emit)  # piles onto it
        captured_flush[0]()
        assert emit.call_args_list[-1].args == ([draft, extra], False)

    def test_reset_drops_pending_flush(
        self, buffer: ResultBuffer, emit: MagicMock, captured_flush: list[Callable[[], None]]
    ) -> None:
        buffer.enqueue(effects.render_results([Result(name="base")], append=False, final=False), emit)  # schedules
        buffer.enqueue(effects.render_results([Result(name="late")], append=True, final=False), emit)  # batched in
        emit.reset_mock()
        buffer.reset()
        captured_flush[0]()  # a flush that fires after the query changed must do nothing
        emit.assert_not_called()
