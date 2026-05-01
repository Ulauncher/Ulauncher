from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

from ulauncher.gi import GioUnix
from ulauncher.modes.apps.app_result import AppResult

# Note: These mock apps actually need real values for Exec or Icon, or they won't load,
# and they need to load from actual files or get_id() and get_filename() will return None
ENTRIES_DIR = Path(__file__).parent.joinpath("mock_desktop_entries").resolve()


class TestAppResult:
    @pytest.fixture(autouse=True)
    def patch_desktop_app_info_new(self, mocker: MockerFixture) -> Any:
        def mkappinfo(app_id: str) -> GioUnix.DesktopAppInfo | None:
            return GioUnix.DesktopAppInfo.new_from_filename(f"{ENTRIES_DIR}/{app_id}")

        return mocker.patch("ulauncher.modes.apps.app_result.GioUnix.DesktopAppInfo.new", new=mkappinfo)

    @pytest.fixture
    def app1(self) -> AppResult | None:
        return AppResult.from_id("trueapp.desktop")

    def test_get_name(self, app1: AppResult) -> None:
        assert app1.name == "TrueApp - Full Name"

    def test_get_description(self, app1: AppResult) -> None:
        assert app1.description == "Your own yes-man"

    def test_icon(self, app1: AppResult) -> None:
        assert app1.icon == "dialog-yes"

    def test_search_score(self, app1: AppResult) -> None:
        assert app1.search_score("true") > app1.search_score("trivago")
