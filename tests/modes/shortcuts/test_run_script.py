import os
import textwrap
from random import randint

from ulauncher.modes.shortcuts.run_script import run_script


class TestRunScriptAction:
    def test_run_with_arg(self) -> None:
        test_file = f"/tmp/ulauncher_test_{randint(1, 111111)}"
        arg = "hello world"
        # RunScriptAction only supports bash argument placeholders ("$@" or "$1")
        # Shortcuts also support "%s", but that should be handled before they get here.
        script = textwrap.dedent(
            f"""\
                #!/bin/bash
                echo $@ > {test_file}
            """
        )
        thread = run_script(script, arg)
        thread.join()
        with open(test_file) as f:
            assert f.read() == f"{arg}\n"
        os.remove(test_file)
