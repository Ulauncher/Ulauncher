from __future__ import annotations

from ulauncher.modes.apps.app_starts import AppStarts as AppStarts_


class AppStarts(AppStarts_):
    def save(self) -> bool:
        return False


class TestAppStarts:
    def test_get_top_app_ids_sorted_by_count(self) -> None:
        app_starts = AppStarts({"app1.desktop": 3000, "app2.desktop": 765})
        ids = app_starts.get_top_app_ids()
        assert ids[0] == "app1.desktop"
        assert ids[1] == "app2.desktop"

    def test_bump_increments_count(self) -> None:
        app_starts = AppStarts({"app.desktop": 100})
        app_starts.bump("app.desktop")
        assert app_starts.get("app.desktop") == 101

    def test_bump_updates_top_app_ids(self) -> None:
        app_starts = AppStarts({"app1.desktop": 1, "app2.desktop": 1})
        app_starts.bump("app2.desktop")
        assert app_starts.get_top_app_ids() == ["app2.desktop", "app1.desktop"]
