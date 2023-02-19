import os
from random import randint
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction


class TestRunScriptAction:
    def test_run_with_arg(self):
        test_file = f"/tmp/ulauncher_test_{randint(1, 111111)}"
        arg = "hello world"
        # RunScriptAction only supports bash argument placeholders ("$@" or "$1")
        # Shortcuts also support "%s", but that should be handled before they get here.
        RunScriptAction(f"#!/bin/bash\necho $@ > {test_file}", arg).run()
        with open(test_file, "r") as f:
            assert f.read() == f"{arg}\n"
        os.remove(test_file)
