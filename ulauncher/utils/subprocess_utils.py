from __future__ import annotations

import subprocess
from typing import Callable

from ulauncher.gi import Gio, GLib

# callback(stdout, error): exactly one is set. On success error is None and stdout is the
# captured standard output. On failure stdout is None and error is an exception (a
# subprocess.CalledProcessError for non-zero exits, or GLib.Error for spawn/communicate failures).
# The inner quotes keep the PEP 604 unions as strings so this evaluates on Python 3.8.
CommandCallback = Callable[["str | None", "Exception | None"], None]


def run_command(cmd: list[str], callback: CommandCallback, *, cwd: str | None = None) -> None:
    """Run a one-shot command via Gio.Subprocess and deliver its stdout (or error) to callback."""
    launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE)
    if cwd:
        launcher.set_cwd(cwd)

    try:
        proc = launcher.spawnv(cmd)
    except GLib.Error as error:
        # spawnv raises synchronously; schedule via idle_add so the callback fires
        # inside the caller's main loop iteration rather than before loop.run().
        GLib.idle_add(callback, None, error)
        return

    def on_done(subprocess_: Gio.Subprocess, result: Gio.AsyncResult) -> None:
        try:
            _, stdout, stderr = subprocess_.communicate_utf8_finish(result)
        except GLib.Error as error:
            callback(None, error)
            return
        if not subprocess_.get_successful():
            exit_status = subprocess_.get_exit_status()
            callback(None, subprocess.CalledProcessError(exit_status, cmd, output=stdout, stderr=stderr))
            return
        callback(stdout, None)

    proc.communicate_utf8_async(None, None, on_done)
