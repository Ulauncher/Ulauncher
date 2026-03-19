import textwrap
from pathlib import Path
from unittest.mock import patch

from ulauncher.modes.shortcuts.run_script import run_script


class TestRunScript:
    # tmp_path is a pytest fixture that cleans up after itself.
    # https://docs.pytest.org/en/stable/reference/reference.html#tmp-path
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
        thread = run_script(script, arg)
        thread.join()
        assert test_file.read_text() == f"{arg}\n"

    def test_run_without_shebang(self, tmp_path: Path) -> None:
        # shell=True means the shell invokes the temp file directly. If the kernel
        # returns ENOEXEC (no shebang / unrecognised format), the shell falls back to
        # interpreting the file as a shell script, so shebang-less scripts work fine.
        test_file = tmp_path / "test_output.txt"
        script = f"echo hello > {test_file}\n"
        thread = run_script(script, "")
        thread.join()
        assert test_file.read_text().strip() == "hello"

    def test_temp_file_cleaned_up_on_success(self) -> None:
        with patch("ulauncher.modes.shortcuts.run_script.os.remove") as mock_remove:
            thread = run_script("#!/bin/sh\ntrue", "")
            thread.join()
        mock_remove.assert_called_once()

    def test_temp_file_cleaned_up_on_script_failure(self) -> None:
        with patch("ulauncher.modes.shortcuts.run_script.os.remove") as mock_remove:
            thread = run_script("#!/bin/bash\nexit 1", "")
            thread.join()
        mock_remove.assert_called_once()
