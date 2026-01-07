from __future__ import annotations  # noqa: N999

import logging

from ulauncher.internals import effects
from ulauncher.modes.shortcuts.run_script import run_script

logger = logging.getLogger()


def RunScriptAction(script: str, arg: str = "") -> effects.CloseWindow:  # noqa: N802
    if not isinstance(script, str):
        msg = f'Script argument "{script}" is invalid. It must be a string'
        raise TypeError(msg)
    if not script:
        msg = "Script argument cannot be empty"
        raise ValueError(msg)
    run_script(script, arg)
    return effects.close_window()
