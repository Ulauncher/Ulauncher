from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from ulauncher.gi import GLib
from ulauncher.utils.subprocess_utils import download_file, run_command


def _drive(
    start: Callable[[Callable[[Any], None], Callable[[Exception], None]], None], timeout_ms: int = 10000
) -> tuple[Any, Exception | None]:
    """Run a callback-based helper to completion under a private GLib main loop."""
    box: dict[str, Any] = {}
    completed = False
    loop = GLib.MainLoop()

    def on_success(result: Any) -> None:
        nonlocal completed
        box["result"], box["error"] = result, None
        completed = True
        loop.quit()

    def on_error(error: Exception) -> None:
        nonlocal completed
        box["result"], box["error"] = None, error
        completed = True
        loop.quit()

    def on_timeout() -> bool:
        box["timeout"] = True
        loop.quit()
        return False

    source_id = GLib.timeout_add(timeout_ms, on_timeout)
    start(on_success, on_error)
    # Skip the loop if a callback already fired synchronously; an early quit() is forgotten.
    if not completed:
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


def test_run_command_spawn_failure_does_not_hang_private_loop() -> None:
    """A spawn error must reach a caller driving run_command under a private thread-default loop,
    as _run_gio_blocking does; GLib.idle_add would post to the default context it never iterates."""
    context = GLib.MainContext.new()
    context.push_thread_default()
    box: dict[str, Any] = {}
    completed = False
    loop = GLib.MainLoop.new(context, False)

    def finish(result: Any = None, error: Exception | None = None) -> None:
        nonlocal completed
        box["result"], box["error"] = result, error
        completed = True
        loop.quit()

    def on_timeout() -> bool:
        box["timeout"] = True
        loop.quit()
        return False

    # Attach the hang guard to the private context; GLib.timeout_add would target the default one.
    timeout_source = GLib.timeout_source_new(2000)
    timeout_source.set_callback(lambda *_: on_timeout())
    timeout_source.attach(context)

    try:
        run_command(["definitely-not-a-real-binary-xyz"], finish, lambda error: finish(error=error))
        if not completed:
            loop.run()
        timeout_source.destroy()
    finally:
        context.pop_thread_default()

    assert "timeout" not in box, "spawn error never reached the private loop (hang)"
    assert isinstance(box["error"], GLib.Error)


def test_download_file_success(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    src.write_text("payload")
    dest = tmp_path / "out.txt"
    result, error = _drive(lambda ok, err: download_file(src.as_uri(), str(dest), ok, err))
    assert error is None
    assert result == str(dest)
    assert dest.read_text() == "payload"


def test_download_file_failure(tmp_path: Path) -> None:
    dest = tmp_path / "out.txt"
    result, error = _drive(lambda ok, err: download_file("file:///nonexistent/nope.txt", str(dest), ok, err))
    assert result is None
    assert error is not None
