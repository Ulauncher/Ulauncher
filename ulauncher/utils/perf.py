from __future__ import annotations

import logging
from dataclasses import dataclass, field
from threading import local
from time import perf_counter
from typing import Optional

logger = logging.getLogger("ulauncher.perf")
_state = local()


def _get_thread_recorder() -> Optional["PerfRecorder"]:
    return getattr(_state, "recorder", None)


def _set_thread_recorder(recorder: Optional["PerfRecorder"]) -> None:
    if recorder is None:
        if hasattr(_state, "recorder"):
            delattr(_state, "recorder")
    else:
        _state.recorder = recorder


@dataclass
class PerfRecorder:
    label: str
    start_time: float = field(default_factory=perf_counter)
    last_time: float = field(init=False)
    active: bool = True

    def __post_init__(self) -> None:
        self.last_time = self.start_time

    def checkpoint(self, name: str) -> None:
        if not self.active:
            return
        now = perf_counter()
        delta = now - self.last_time
        total = now - self.start_time
        logger.info("perf:%s %s +%.3fs (%.3fs total)", self.label, name, delta, total)
        self.last_time = now

    def finish(self, name: str = "done") -> None:
        if not self.active:
            return
        self.checkpoint(name)
        self.active = False
        if _get_thread_recorder() is self:
            _set_thread_recorder(None)


def start_trace(label: str) -> PerfRecorder:
    recorder = PerfRecorder(label=label)
    _set_thread_recorder(recorder)
    recorder.checkpoint("start")
    return recorder


def get_current() -> Optional[PerfRecorder]:
    return _get_thread_recorder()


def set_current(recorder: Optional[PerfRecorder]) -> None:
    _set_thread_recorder(recorder)
