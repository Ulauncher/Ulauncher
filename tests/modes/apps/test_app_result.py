from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

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

    @pytest.fixture(autouse=True)
    def patch_desktop_app_info_get_all(self, mocker: MockerFixture) -> Any:
        def get_all_appinfo() -> list[GioUnix.DesktopAppInfo]:
            return [
                app_info
                for path in ["trueapp.desktop", "falseapp.desktop"]
                if (app_info := GioUnix.DesktopAppInfo.new_from_filename(f"{ENTRIES_DIR}/{path}"))
            ]

        return mocker.patch("ulauncher.modes.apps.app_result.GioUnix.DesktopAppInfo.get_all", new=get_all_appinfo)

    @pytest.fixture
    def app1(self) -> AppResult | None:
        return AppResult.from_id("trueapp.desktop")

    @pytest.fixture
    def app2(self) -> AppResult | None:
        return AppResult.from_id("falseapp.desktop")

    @pytest.fixture(autouse=True)
    def mock_app_starts(self, mocker: MockerFixture) -> dict[str, int]:
        class _MockStarts(Dict[str, int]):
            def save(self) -> None:
                pass

        app_starts_data: dict[str, int] = _MockStarts({"falseapp.desktop": 3000, "trueapp.desktop": 765})
        mocker.patch("ulauncher.modes.apps.app_result.app_starts", app_starts_data)
        return app_starts_data

    def test_get_name(self, app1: AppResult) -> None:
        assert app1.name == "TrueApp - Full Name"

    def test_get_description(self, app1: AppResult) -> None:
        assert app1.description == "Your own yes-man"

    def test_icon(self, app1: AppResult) -> None:
        assert app1.icon == "dialog-yes"

    def test_search_score(self, app1: AppResult) -> None:
        assert app1.search_score("true") > app1.search_score("trivago")

    def test_bump(self, app1: AppResult, mock_app_starts: dict[str, int]) -> None:
        app1.bump_starts()
        assert mock_app_starts.get("trueapp.desktop") == 766
