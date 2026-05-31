from __future__ import annotations

import subprocess
import sys
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
            # if killed by a signal: report it as a negative status (subprocess convention)
            exit_status = subprocess_.get_exit_status() if subprocess_.get_if_exited() else -subprocess_.get_term_sig()
            callback(None, subprocess.CalledProcessError(exit_status, cmd, output=stdout, stderr=stderr))
            return
        callback(stdout, None)

    proc.communicate_utf8_async(None, None, on_done)


# Run Python/urllib.request inside a Gio.Subprocess to avoid needing a dependency like libsoup, gvfsd-http, curl or wget
_DOWNLOAD_SCRIPT = (
    "import sys, urllib.request, shutil; "
    "r = urllib.request.urlopen(sys.argv[1], timeout=30); "
    "f = open(sys.argv[2], 'wb'); "
    "shutil.copyfileobj(r, f); "
    "f.close(); r.close()"
)

# callback(dest_path, error): dest_path is the saved file path on success, error is set on failure.
DownloadCallback = Callable[["str | None", "Exception | None"], None]


def download_file(url: str, dest_path: str, callback: DownloadCallback) -> None:
    """Download url to dest_path without blocking. See _DOWNLOAD_SCRIPT for why this spawns Python."""

    def on_done(_stdout: str | None, error: Exception | None) -> None:
        if error:
            callback(None, error)
            return
        callback(dest_path, None)

    run_command([sys.executable, "-c", _DOWNLOAD_SCRIPT, url, dest_path], on_done)
