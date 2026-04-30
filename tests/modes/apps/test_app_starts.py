from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.modes.apps.app_starts import AppStarts


class TestAppStarts:
    @pytest.fixture(autouse=True)
    def mock_app_starts(self, mocker: MockerFixture) -> AppStarts:
        class _MockStarts(AppStarts):
            def save(self) -> None:  # type: ignore[override]
                pass

        instance = _MockStarts()
        instance.update({"falseapp.desktop": 3000, "trueapp.desktop": 765})
        self.save_spy: MagicMock = mocker.spy(instance, "save")
        return instance

    def test_get_top_app_ids_sorted_by_count(self, mock_app_starts: AppStarts) -> None:
        ids = mock_app_starts.get_top_app_ids()
        assert ids[0] == "falseapp.desktop"
        assert ids[1] == "trueapp.desktop"

    def test_bump_increments_count(self, mock_app_starts: AppStarts) -> None:
        mock_app_starts.bump("trueapp.desktop")
        assert mock_app_starts.get("trueapp.desktop") == 766
        self.save_spy.assert_called_once()

    def test_bump_invalidates_cache(self, mock_app_starts: AppStarts) -> None:
        mock_app_starts.get_top_app_ids()  # populate cache
        mock_app_starts.bump("trueapp.desktop")
        assert mock_app_starts._top_ids is None
