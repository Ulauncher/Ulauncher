from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from ulauncher.utils import scheduling

if TYPE_CHECKING:
    from ulauncher.internals import effects
    from ulauncher.internals.result import Result

RENDER_THROTTLE = 0.05  # delay in sec to coalesce streamed result batches

EmitResults = Callable[["list[Result]", bool], None]


class ResultBuffer:
    """In-flight stream of result batches for a query, holding the buffered results, whether they
    replace or append, and the throttle timer between paints."""

    def __init__(self) -> None:
        self._buffer: list[Result] | None = None
        self._painted = False  # a batch has been painted, so there is a displayed list to append onto
        self._is_appending = False
        self._timer: scheduling.Context | None = None
        self._emit: EmitResults | None = None

    def reset(self) -> None:
        """Drop buffered batches and any scheduled paint so the next query starts clean."""
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self._buffer = None
        self._painted = False
        self._is_appending = False
        self._emit = None

    def enqueue(self, effect: effects.RenderResults, emit: EmitResults) -> None:
        self._emit = emit
        is_append = effect.get("append", False)
        if is_append and self._buffer is not None:
            self._buffer += effect["results"]
        else:
            self._buffer = list(effect["results"])
            self._is_appending = is_append

        if effect.get("final", True):
            self._paint()
        elif not self._timer:
            self._timer = scheduling.timer(RENDER_THROTTLE, self._throttled_paint)

    def _throttled_paint(self) -> None:
        # the throttle timer fired; ignore it if reset() cancelled us in the meantime
        if self._timer is not None:
            self._paint()

    def _paint(self) -> None:
        if self._emit is None or self._buffer is None:
            return

        append = self._painted and self._is_appending
        results = self._buffer
        emit = self._emit
        self.reset()
        self._painted = True
        emit(results, append)
