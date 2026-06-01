from __future__ import annotations

import os
import textwrap
from pathlib import Path
from unittest.mock import patch

from ulauncher.gi import GLib
from ulauncher.modes.shortcuts.run_script import run_script


def _drive_run_script(script: str, arg: str, timeout_ms: int = 10000) -> list[str]:
    """Run run_script under a private GLib main loop, returning the paths it cleaned up.

    run_script is fire-and-forget, so we hook its final action (deleting the temp file) to know
    when the subprocess has finished and quit the loop.
    """
    loop = GLib.MainLoop()
    removed: list[str] = []
    real_remove = os.remove  # captured before patching; the patch replaces os.remove globally

    def fake_remove(path: str) -> None:
        removed.append(path)
        real_remove(path)
        loop.quit()

    def on_timeout() -> bool:
        loop.quit()
        return False

    with patch("ulauncher.modes.shortcuts.run_script.os.remove", side_effect=fake_remove):
        source_id = GLib.timeout_add(timeout_ms, on_timeout)
        run_script(script, arg)
        loop.run()
        timed_out = not removed
        if not timed_out:
            GLib.source_remove(source_id)
        assert not timed_out, "run_script did not finish before timeout"

    return removed


class TestRunScript:
    def test_run_with_arg(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_output.txt"
        arg = "hello world"
        # run_script only supports bash argument placeholders ("$@" or "$1")
        # Shortcuts also support "%s", but that should be handled before they get here.
        script = textwrap.dedent(
            f"""\
                #!/bin/bash
                echo $@ > {test_file}
            """
        )
        _drive_run_script(script, arg)
        assert test_file.read_text() == f"{arg}\n"

    def test_run_without_shebang(self, tmp_path: Path) -> None:
        # `sh -c` invokes the temp file directly. If the kernel returns ENOEXEC (no shebang /
        # unrecognised format), the shell falls back to interpreting the file as a shell script,
        # so shebang-less scripts work fine.
        test_file = tmp_path / "test_output.txt"
        script = f"echo hello > {test_file}\n"
        _drive_run_script(script, "")
        assert test_file.read_text().strip() == "hello"

    def test_no_arg_passes_no_positional_params(self, tmp_path: Path) -> None:
        # An empty arg must not be passed as a positional parameter, so $# stays 0.
        test_file = tmp_path / "test_output.txt"
        script = f"#!/bin/sh\necho $# > {test_file}\n"
        _drive_run_script(script, "")
        assert test_file.read_text().strip() == "0"

    def test_arg_passed_as_single_positional_param(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test_output.txt"
        script = f"#!/bin/sh\necho $# > {test_file}\n"
        _drive_run_script(script, "some arg")
        assert test_file.read_text().strip() == "1"

    def test_temp_file_cleaned_up_on_success(self) -> None:
        removed = _drive_run_script("#!/bin/sh\ntrue", "")
        assert len(removed) == 1

    def test_temp_file_cleaned_up_on_script_failure(self) -> None:
        removed = _drive_run_script("#!/bin/bash\nexit 1", "")
        assert len(removed) == 1
