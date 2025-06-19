from __future__ import annotations

import re

from ulauncher.api import actions
from ulauncher.modes.shortcuts.run_script import run_script


def run_shortcut(command: str, arg: str | None = None) -> bool | str | actions.Action[str]:
    command = command.strip()
    if arg:
        command = command.replace("%s", arg)
    if re.match(r"^http(s)?://", command):
        return actions.open(command)
    run_script(command, arg or "")
    return False
