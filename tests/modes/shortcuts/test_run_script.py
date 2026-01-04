import textwrap
from pathlib import Path

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
