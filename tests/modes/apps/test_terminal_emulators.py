from __future__ import annotations

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from ulauncher.gi import GioUnix
from ulauncher.modes.apps.terminal_emulators import TerminalEmulator, get_terminal_emulators

ENTRIES_DIR = Path(__file__).parent.joinpath("mock_desktop_entries").resolve()


def _entry(name: str, exec_line: str, exec_arg: str | None = None, hidden: bool = False) -> str:
    lines = [
        "[Desktop Entry]",
        f"Name={name}",
        f"Exec={exec_line}",
        "Categories=System;TerminalEmulator;",
    ]
    if exec_arg is not None:
        lines.append(f"X-TerminalArgExec={exec_arg}")
    if hidden:
        lines.append("NoDisplay=true")
    lines.append("Type=Application")
    return "\n".join(lines) + "\n"


# (name, Exec, X-TerminalArgExec, NoDisplay). "" as exec_arg means the key is set but empty, i.e. no flag
ENTRY_SPECS = [
    ("TermEmptyArg", "sh", "", False),
    ("TermKnownArg", "false", None, False),
    ("TermUnknown", "env", None, False),
    ("TermWithArg", "true --window", "--", False),
    ("TermHidden", "true --preferences", None, True),
]


@pytest.fixture(autouse=True)
def terminal_entries(tmp_path: Path, mocker: MockerFixture) -> None:
    apps = []
    for name, exec_line, exec_arg, hidden in ENTRY_SPECS:
        entry_path = tmp_path / f"{name.lower()}.desktop"
        entry_path.write_text(_entry(name, exec_line, exec_arg, hidden))
        apps.append(GioUnix.DesktopAppInfo.new_from_filename(str(entry_path)))
    # trueapp is not a terminal; verifies entries without the TerminalEmulator category are filtered out
    apps.append(GioUnix.DesktopAppInfo.new_from_filename(f"{ENTRIES_DIR}/trueapp.desktop"))
    mocker.patch("ulauncher.modes.apps.terminal_emulators.GioUnix.DesktopAppInfo.get_all", return_value=apps)


def test_get_terminal_emulators(mocker: MockerFixture) -> None:
    # "true" has a desktop entry, so it must not be listed a second time from PATH
    mocker.patch.dict(
        "ulauncher.modes.apps.terminal_emulators.EXEC_ARG_BY_EXECUTABLE",
        {"cat": "-e", "false": "-x", "true": "-e", "ulauncher-test-missing-terminal": "-e"},
        clear=True,
    )

    assert get_terminal_emulators() == [
        TerminalEmulator("cat", "cat", "cat -e"),
        TerminalEmulator("TermEmptyArg", "sh", "sh"),
        TerminalEmulator("TermKnownArg", "false", "false -x"),
        TerminalEmulator("TermWithArg", "true", "true --window --"),
    ]
