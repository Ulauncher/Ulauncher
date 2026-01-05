from __future__ import annotations

import re

from ulauncher.internals import effects
from ulauncher.modes.shortcuts.run_script import run_script


def run_shortcut(command: str, arg: str | None = None) -> effects.EffectMessage:
    command = command.strip()
    if arg:
        command = command.replace("%s", arg)
    if re.match(r"^http(s)?://", command):
        return effects.open(command)
    run_script(command, arg or "")
    return effects.close_window()
