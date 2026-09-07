from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from pytest_mock import MockerFixture

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import upgrade


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

    assert upgrade.run(CLIArguments(input="com.example.theme")) == 0
    check_update.assert_called_once()
    download.assert_called_once()


def test_run__single_theme_upgrade_no_update_skips_download(mocker: MockerFixture) -> None:
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

    assert upgrade.run(CLIArguments(input="com.example.theme")) == 0
    download.assert_not_called()


def test_run__batch_upgrades_installed_themes(mocker: MockerFixture) -> None:
    mocker.patch.object(upgrade, "get_ext_registry", return_value=SimpleNamespace(iterate=list))
    mocker.patch.object(upgrade.theme_installer, "installed_ids", return_value=["com.example.theme"])
    check_update, download = _mock_theme_install(mocker)

    assert upgrade.run(CLIArguments()) == 0
    check_update.assert_called_once()
    download.assert_called_once()


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

    assert upgrade.run(CLIArguments()) == 0
    check_update.assert_not_called()
