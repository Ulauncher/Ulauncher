from __future__ import annotations

import shutil
from pathlib import Path
from typing import NamedTuple

from ulauncher.gi import GioUnix
from ulauncher.modes.apps.launch_app import get_exec

# Only these terminals, and those whose desktop entry sets X-TerminalArgExec, are offered. Guessing a flag for
# others fails silently, and some (sakura, warp) can't take the command and its arguments as separate argv items.
EXEC_ARG_BY_EXECUTABLE = {
    "alacritty": "-e",
    "blackbox-terminal": "--",
    "cosmic-term": "-e",
    "deepin-terminal": "-e",
    "foot": "--",
    "ghostty": "-e",
    "gnome-terminal": "--",
    "io.elementary.terminal": "-x",
    "kgx": "-e",
    "kitty": "--",
    "konsole": "-e",
    "lxterminal": "-e",
    "mate-terminal": "-x",
    "ptyxis": "--",
    "qterminal": "-e",
    "roxterm": "-x",
    "st": "-e",
    "terminator": "-x",
    "tilix": "-e",
    "urxvt": "-e",
    "wezterm": "--",
    "xfce4-terminal": "-x",
    "xterm": "-e",
}


class TerminalEmulator(NamedTuple):
    name: str
    executable_name: str
    command: str


def _get_exec_arg(app: GioUnix.DesktopAppInfo, executable_name: str) -> str | None:
    # An empty value is valid and means the terminal takes the command without a flag
    exec_arg = app.get_string("X-TerminalArgExec")
    if exec_arg is not None:
        return exec_arg
    return EXEC_ARG_BY_EXECUTABLE.get(executable_name)


def get_terminal_emulators() -> list[TerminalEmulator]:
    """List installed terminal emulators with the command that runs a program in each."""
    terminals: dict[str, TerminalEmulator] = {}
    executable_names = set()
    for app in GioUnix.DesktopAppInfo.get_all():
        if "TerminalEmulator" not in (app.get_categories() or "").split(";") or app.get_nodisplay():
            continue
        exec_line = get_exec(app)
        executable = app.get_executable()
        if not exec_line or not executable:
            continue
        executable_name = Path(executable).name
        executable_names.add(executable_name)
        exec_arg = _get_exec_arg(app, executable_name)
        if exec_arg is not None:
            command = f"{exec_line} {exec_arg}".strip()
            terminals.setdefault(command, TerminalEmulator(app.get_display_name(), executable_name, command))

    for name, exec_arg in EXEC_ARG_BY_EXECUTABLE.items():
        if name not in executable_names and shutil.which(name):
            command = f"{name} {exec_arg}"
            terminals.setdefault(command, TerminalEmulator(name, name, command))

    return sorted(terminals.values(), key=lambda terminal: terminal.name.lower())
