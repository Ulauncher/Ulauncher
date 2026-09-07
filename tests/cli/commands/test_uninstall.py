from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from pytest_mock import MockerFixture

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import uninstall


def _args() -> CLIArguments:
    return CLIArguments(input="com.example.repo")


def test_run__collision_uninstalls_both(mocker: MockerFixture) -> None:
    record: Any = SimpleNamespace(id="com.example.repo", path="/ext", is_manageable=True)
    mocker.patch.object(uninstall, "get_ext_record", return_value=record)
    mocker.patch.object(uninstall, "get_theme_id", return_value="com.example.repo")
    registry = SimpleNamespace(uninstall=mocker.Mock(side_effect=lambda _rec, ok, _fail: ok()))
    mocker.patch.object(uninstall, "get_ext_registry", return_value=registry)
    theme_uninstall = mocker.patch.object(uninstall.theme_installer, "uninstall")
    dbus = mocker.patch.object(uninstall, "dbus_trigger_event")

    assert uninstall.run(_args()) == 0
    registry.uninstall.assert_called_once()
    theme_uninstall.assert_called_once_with("com.example.repo")
    assert dbus.call_count == 2


def test_run__no_match_returns_error(mocker: MockerFixture) -> None:
    mocker.patch.object(uninstall, "get_ext_record", return_value=None)
    mocker.patch.object(uninstall, "get_theme_id", return_value=None)
    assert uninstall.run(_args()) == 1


def test_run__theme_uninstall(mocker: MockerFixture) -> None:
    mocker.patch.object(uninstall, "get_ext_record", return_value=None)
    mocker.patch.object(uninstall, "get_theme_id", return_value="com.example.theme")
    theme_uninstall = mocker.patch.object(uninstall.theme_installer, "uninstall")
    dbus = mocker.patch.object(uninstall, "dbus_trigger_event")

    assert uninstall.run(_args()) == 0
    theme_uninstall.assert_called_once_with("com.example.theme")
    dbus.assert_called_once_with("themes:reload")


def test_run__theme_uninstall_failure_returns_error(mocker: MockerFixture) -> None:
    mocker.patch.object(uninstall, "get_ext_record", return_value=None)
    mocker.patch.object(uninstall, "get_theme_id", return_value="com.example.theme")
    mocker.patch.object(uninstall.theme_installer, "uninstall", side_effect=OSError("denied"))
    dbus = mocker.patch.object(uninstall, "dbus_trigger_event")

    assert uninstall.run(_args()) == 1
    dbus.assert_not_called()
