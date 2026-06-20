from __future__ import annotations

from typing import Callable
from unittest.mock import MagicMock, PropertyMock

from pytest_mock import MockerFixture

from ulauncher.core import UlauncherCore
from ulauncher.internals import effects
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result


class TestStreamingResults:
    """Core wires streamed RENDER_RESULTS through the buffer; ResultBuffer owns the batching
    behavior itself (see tests/internals/test_result_buffer.py)."""

    def test_streamed_render_stamps_query_and_pick(self, mocker: MockerFixture) -> None:
        core = UlauncherCore()
        core.query = Query(None, "foo")
        mocker.patch.object(UlauncherCore, "last_query_result_pick", new_callable=PropertyMock, return_value="picked")
        outer = MagicMock()
        emit = core._mode_callback(None, outer)  # valid_mode=None skips the active-mode staleness guard

        r = Result(name="a")
        emit(effects.render_results([r], append=False, final=True))

        update = outer.call_args.args[0]
        assert update["results"] == [r]
        assert update["append"] is False
        assert str(update["query"]) == "foo"
        assert update["selected_name"] == "picked"

    def test_activating_drops_pending_stream_paint(self, mocker: MockerFixture) -> None:
        # A throttled paint armed mid-stream must not fire over what an activation renders next.
        core = UlauncherCore()
        captured: list[Callable[[], None]] = []
        mocker.patch(
            "ulauncher.internals.result_buffer.scheduling.timer",
            side_effect=lambda _d, fn: (captured.append(fn), MagicMock())[1],
        )
        render = MagicMock()
        core._mode_callback(None, render)(effects.render_results([Result(name="a")], final=False))
        assert captured  # a flush was scheduled
        render.assert_not_called()  # but it hasn't painted yet

        core.activate_result(Result(name="a"), MagicMock(), alt=True)
        captured[0]()  # the stale flush fires after activation
        render.assert_not_called()
