from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.data import Ok
from ulauncher.gi import GioUnix
from ulauncher.modes.apps.launch_app import launch_app
from ulauncher.utils.settings import Settings
from ulauncher.utils.systemd_controller import SystemdUnitStatus

TERMAPP_ENTRY = """[Desktop Entry]
Name=TermApp
Exec=true --flag %F
Icon=utilities-terminal
Terminal=true
Type=Application
"""


@pytest.fixture(autouse=True)
def termapp(tmp_path: Path, mocker: MockerFixture) -> None:
    # DesktopAppInfo parses only real files, and launch_app resolves the entry by app id, hence the `new` patch
    (tmp_path / "termapp.desktop").write_text(TERMAPP_ENTRY)
    mocker.patch(
        "ulauncher.modes.apps.launch_app.GioUnix.DesktopAppInfo.new",
        new=lambda app_id: GioUnix.DesktopAppInfo.new_from_filename(str(tmp_path / app_id)),
    )


@pytest.fixture
def launch_detached(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("ulauncher.modes.apps.launch_app.launch_detached")


@pytest.fixture
def emit(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("ulauncher.modes.apps.launch_app.events.emit")


def set_terminal_command(mocker: MockerFixture, terminal_command: str) -> None:
    settings = Settings(terminal_command=terminal_command)
    mocker.patch("ulauncher.modes.apps.launch_app.Settings.load", return_value=settings)


def test_custom_terminal_gets_exec_as_argv(mocker: MockerFixture, launch_detached: MagicMock, emit: MagicMock) -> None:
    set_terminal_command(mocker, "true -e")
    assert launch_app("termapp.desktop")
    launch_detached.assert_called_once_with(["true", "-e", "true", "--flag"], None, startup_notify_id=None)
    emit.assert_not_called()


@pytest.mark.parametrize("terminal_command", ["ulauncher-test-missing-terminal -e", "unclosed 'quote"])
def test_unrunnable_custom_terminal_falls_back_to_default(
    mocker: MockerFixture, launch_detached: MagicMock, emit: MagicMock, terminal_command: str
) -> None:
    set_terminal_command(mocker, terminal_command)
    assert launch_app("termapp.desktop")
    launch_detached.assert_called_once_with(["gtk-launch", "termapp"], None, startup_notify_id=None)
    assert emit.call_args.args[0] == "app:show_notification"


@pytest.fixture
def spawn_async(mocker: MockerFixture) -> MagicMock:
    """Let the real launch_detached run and capture the child env it spawns with."""
    mocker.patch(
        "ulauncher.utils.launch_detached.SystemdController",
        return_value=mocker.Mock(status=lambda: Ok(SystemdUnitStatus([]))),
    )
    return mocker.patch("ulauncher.utils.launch_detached.GLib.spawn_async")


@pytest.mark.parametrize(("startup_notify", "expected"), [("true", "TOKEN"), ("false", None)])
def test_launch_env_gets_startup_id_if_the_entry_opts_in(
    tmp_path: Path,
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    spawn_async: MagicMock,
    startup_notify: str,
    expected: str | None,
) -> None:
    # A terminal launched with startup notification passes these on to the test run
    monkeypatch.delenv("XDG_ACTIVATION_TOKEN", raising=False)
    monkeypatch.delenv("DESKTOP_STARTUP_ID", raising=False)
    (tmp_path / "app.desktop").write_text(
        f"[Desktop Entry]\nName=App\nExec=true\nType=Application\nStartupNotify={startup_notify}\n"
    )
    context = mocker.Mock(get_startup_notify_id=mocker.Mock(return_value="TOKEN"))
    mocker.patch("ulauncher.modes.apps.launch_app.get_launch_context", return_value=context)

    assert launch_app("app.desktop")

    env = dict(item.split("=", 1) for item in spawn_async.call_args.kwargs["envp"])
    assert env.get("XDG_ACTIVATION_TOKEN") == expected
    assert env.get("DESKTOP_STARTUP_ID") == expected
