from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from pytest_mock import MockerFixture

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import upgrade


def _args() -> CLIArguments:
    return CLIArguments(input="com.example.repo")


def test_run__collision_upgrades_both(mocker: MockerFixture) -> None:
    record: Any = SimpleNamespace(id="com.example.repo")
    mocker.patch.object(upgrade, "get_ext_record", return_value=record)
    mocker.patch.object(upgrade, "get_theme_id", return_value="com.example.repo")
    upgrade_one = mocker.patch.object(upgrade, "upgrade_one", return_value=True)
    upgrade_one_theme = mocker.patch.object(upgrade, "upgrade_one_theme", return_value=True)

    assert upgrade.run(_args()) == 0
    upgrade_one.assert_called_once_with(record)
    upgrade_one_theme.assert_called_once_with("com.example.repo")


def test_run__collision_reports_failure_but_attempts_both(mocker: MockerFixture) -> None:
    record: Any = SimpleNamespace(id="com.example.repo")
    mocker.patch.object(upgrade, "get_ext_record", return_value=record)
    mocker.patch.object(upgrade, "get_theme_id", return_value="com.example.repo")
    mocker.patch.object(upgrade, "upgrade_one", return_value=False)
    upgrade_one_theme = mocker.patch.object(upgrade, "upgrade_one_theme", return_value=True)

    assert upgrade.run(_args()) == 1
    upgrade_one_theme.assert_called_once()


def _mock_theme_install(mocker: MockerFixture) -> tuple[Any, Any]:
    """Mock theme_installer so one theme is installed and has an update."""
    mocker.patch.object(
        upgrade.theme_installer,
        "load_state",
        return_value=SimpleNamespace(url="https://example.com/theme", commit_hash="oldhash1234"),
    )
    check_update = mocker.patch.object(
        upgrade.theme_installer, "check_update", side_effect=lambda _id, ok, _err: ok((True, "newhash1234"))
    )
    download = mocker.patch.object(
        upgrade.theme_installer, "download", side_effect=lambda _url, ok, _err, _hash: ok(None)
    )
    return check_update, download


def test_run__single_theme_upgrade_reports_update(mocker: MockerFixture) -> None:
    mocker.patch.object(upgrade, "get_ext_record", return_value=None)
    mocker.patch.object(upgrade, "get_theme_id", return_value="com.example.theme")
    check_update, download = _mock_theme_install(mocker)
    dbus = mocker.patch.object(upgrade, "dbus_trigger_event")

    assert upgrade.run(CLIArguments(input="com.example.theme")) == 0
    check_update.assert_called_once()
    download.assert_called_once()
    dbus.assert_called_once_with("themes:reload")


def test_run__single_theme_upgrade_no_update_skips_download_and_reload(mocker: MockerFixture) -> None:
    mocker.patch.object(upgrade, "get_ext_record", return_value=None)
    mocker.patch.object(upgrade, "get_theme_id", return_value="com.example.theme")
    mocker.patch.object(
        upgrade.theme_installer,
        "load_state",
        return_value=SimpleNamespace(url="https://example.com/theme", commit_hash="oldhash1234"),
    )
    download = mocker.patch.object(upgrade.theme_installer, "download")
    mocker.patch.object(
        upgrade.theme_installer, "check_update", side_effect=lambda _id, ok, _err: ok((False, "oldhash1234"))
    )
    dbus = mocker.patch.object(upgrade, "dbus_trigger_event")

    assert upgrade.run(CLIArguments(input="com.example.theme")) == 0
    download.assert_not_called()
    dbus.assert_not_called()


def test_run__batch_upgrades_installed_themes(mocker: MockerFixture) -> None:
    mocker.patch.object(upgrade, "get_ext_registry", return_value=SimpleNamespace(iterate=list))
    mocker.patch.object(upgrade.theme_installer, "installed_ids", return_value=["com.example.theme"])
    _mock_theme_install(mocker)
    dbus = mocker.patch.object(upgrade, "dbus_trigger_event")

    assert upgrade.run(CLIArguments()) == 0
    dbus.assert_called_once_with("themes:reload")


def test_run__single_theme_without_source_fails_without_checking(mocker: MockerFixture) -> None:
    mocker.patch.object(upgrade, "get_ext_record", return_value=None)
    mocker.patch.object(upgrade, "get_theme_id", return_value="com.example.theme")
    mocker.patch.object(upgrade.theme_installer, "load_state", return_value=SimpleNamespace(url="", commit_hash=""))
    check_update = mocker.patch.object(upgrade.theme_installer, "check_update")

    assert upgrade.run(CLIArguments(input="com.example.theme")) == 1
    check_update.assert_not_called()


def test_run__batch_skips_themes_without_source(mocker: MockerFixture) -> None:
    mocker.patch.object(upgrade, "get_ext_registry", return_value=SimpleNamespace(iterate=list))
    mocker.patch.object(upgrade.theme_installer, "installed_ids", return_value=["com.example.manual"])
    mocker.patch.object(upgrade.theme_installer, "load_state", return_value=SimpleNamespace(url="", commit_hash=""))
    check_update = mocker.patch.object(upgrade.theme_installer, "check_update")
    dbus = mocker.patch.object(upgrade, "dbus_trigger_event")

    assert upgrade.run(CLIArguments()) == 0
    check_update.assert_not_called()
    dbus.assert_not_called()
