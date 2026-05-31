from __future__ import annotations

import subprocess
import sys
from typing import Any, Callable

from ulauncher.gi import GLib
from ulauncher.utils.subprocess_utils import run_command


def _drive(
    start: Callable[[Callable[[Any], None], Callable[[Exception], None]], None], timeout_ms: int = 10000
) -> tuple[Any, Exception | None]:
    """Run a callback-based helper to completion under a private GLib main loop."""
    box: dict[str, Any] = {}
    loop = GLib.MainLoop()

    def on_success(result: Any) -> None:
        box["result"], box["error"] = result, None
        loop.quit()

    def on_error(error: Exception) -> None:
        box["result"], box["error"] = None, error
        loop.quit()

    def on_timeout() -> bool:
        box["timeout"] = True
        loop.quit()
        return False

    source_id = GLib.timeout_add(timeout_ms, on_timeout)
    start(on_success, on_error)
    loop.run()
    timed_out = "timeout" in box
    if not timed_out:
        GLib.source_remove(source_id)
    assert not timed_out, "callback did not fire before timeout"
    return box["result"], box["error"]


def test_run_command_success() -> None:
    result, error = _drive(lambda ok, err: run_command([sys.executable, "-c", "print('hello')"], ok, err))
    assert error is None
    assert result.strip() == "hello"


def test_run_command_nonzero_exit() -> None:
    result, error = _drive(lambda ok, err: run_command([sys.executable, "-c", "import sys; sys.exit(3)"], ok, err))
    assert result is None
    assert isinstance(error, subprocess.CalledProcessError)
    assert error.returncode == 3


def test_run_command_spawn_failure() -> None:
    result, error = _drive(lambda ok, err: run_command(["definitely-not-a-real-binary-xyz"], ok, err))
    assert result is None
    assert isinstance(error, GLib.Error)
