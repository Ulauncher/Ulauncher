from __future__ import annotations

import subprocess
from typing import Callable

from ulauncher.gi import Gio, GLib

OnSuccess = Callable[[str], None]
OnError = Callable[[Exception], None]  # receives a GLib.Error or subprocess.CalledProcessError for non-zero exits


def run_command(cmd: list[str], on_success: OnSuccess, on_error: OnError, *, cwd: str | None = None) -> None:
    """Run a one-shot command via Gio.Subprocess, delivering its stdout to on_success or an error
    to on_error."""
    launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE)
    if cwd:
        launcher.set_cwd(cwd)

    try:
        proc = launcher.spawnv(cmd)
    except GLib.Error as error:
        # spawnv raises synchronously; schedule via idle_add so on_error fires inside the
        # caller's main loop iteration rather than before loop.run().
        GLib.idle_add(on_error, error)
        return

    def on_done(subprocess_: Gio.Subprocess, result: Gio.AsyncResult) -> None:
        try:
            _, stdout, stderr = subprocess_.communicate_utf8_finish(result)
        except GLib.Error as error:
            on_error(error)
            return
        if not subprocess_.get_successful():
            # if killed by a signal: report it as a negative status (subprocess convention)
            exit_status = subprocess_.get_exit_status() if subprocess_.get_if_exited() else -subprocess_.get_term_sig()
            on_error(subprocess.CalledProcessError(exit_status, cmd, output=stdout, stderr=stderr))
            return
        on_success(stdout)

    proc.communicate_utf8_async(None, None, on_done)
