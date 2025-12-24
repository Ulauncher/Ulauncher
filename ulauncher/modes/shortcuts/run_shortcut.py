from __future__ import annotations

import re

from ulauncher.internals import actions
from ulauncher.internals.result import ActionMessage
from ulauncher.modes.shortcuts.run_script import run_script


def run_shortcut(command: str, arg: str | None = None) -> ActionMessage:
    command = command.strip()
    if arg:
        command = command.replace("%s", arg)
    if re.match(r"^http(s)?://", command):
        return actions.open(command)
    run_script(command, arg or "")
    return actions.close_window()
