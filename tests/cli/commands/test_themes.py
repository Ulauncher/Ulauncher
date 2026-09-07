from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest
from pytest_mock import MockerFixture

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import themes


def test_run__lists_installed_themes(mocker: MockerFixture, caplog: pytest.LogCaptureFixture) -> None:
    mocker.patch.object(themes.theme_installer, "installed_ids", return_value=["com.example.theme"])
    mocker.patch.object(
        themes.theme_installer, "load_state", return_value=SimpleNamespace(url="https://example.com/theme")
    )

    with caplog.at_level(logging.INFO):
        assert themes.run(CLIArguments()) == 0
    assert "com.example.theme" in caplog.text
    assert "https://example.com/theme" in caplog.text


def test_run__no_themes_installed(mocker: MockerFixture, caplog: pytest.LogCaptureFixture) -> None:
    mocker.patch.object(themes.theme_installer, "installed_ids", return_value=[])

    with caplog.at_level(logging.INFO):
        assert themes.run(CLIArguments()) == 0
    assert "No themes installed." in caplog.text
