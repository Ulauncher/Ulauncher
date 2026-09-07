from __future__ import annotations

from pytest_mock import MockerFixture

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import uninstall


def _args() -> CLIArguments:
    return CLIArguments(input="com.example.repo")


def test_run__no_match_returns_error(mocker: MockerFixture) -> None:
    mocker.patch.object(uninstall, "get_ext_record", return_value=None)
    mocker.patch.object(uninstall, "get_theme_id", return_value=None)
    assert uninstall.run(_args()) == 1


def test_run__theme_uninstall(mocker: MockerFixture) -> None:
    mocker.patch.object(uninstall, "get_ext_record", return_value=None)
    mocker.patch.object(uninstall, "get_theme_id", return_value="com.example.theme")
    theme_uninstall = mocker.patch.object(uninstall.theme_installer, "uninstall")

    assert uninstall.run(_args()) == 0
    theme_uninstall.assert_called_once_with("com.example.theme")


def test_run__theme_uninstall_failure_returns_error(mocker: MockerFixture) -> None:
    mocker.patch.object(uninstall, "get_ext_record", return_value=None)
    mocker.patch.object(uninstall, "get_theme_id", return_value="com.example.theme")
    mocker.patch.object(uninstall.theme_installer, "uninstall", side_effect=OSError("denied"))

    assert uninstall.run(_args()) == 1
