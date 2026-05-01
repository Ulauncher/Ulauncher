from __future__ import annotations

from ulauncher.modes.apps.app_history import _AppHistory


class AppHistory(_AppHistory):
    def save(self) -> bool:
        return False


class TestAppHistory:
    def test_get_top_app_ids_sorted_by_count(self) -> None:
        app_history = AppHistory({"app1.desktop": 3000, "app2.desktop": 765})
        ids = app_history.get_top_app_ids()
        assert ids[0] == "app1.desktop"
        assert ids[1] == "app2.desktop"

    def test_bump_increments_count(self) -> None:
        app_history = AppHistory({"app.desktop": 100})
        app_history.bump("app.desktop")
        assert app_history.get("app.desktop") == 101

    def test_bump_updates_top_app_ids(self) -> None:
        app_history = AppHistory({"app1.desktop": 1, "app2.desktop": 1})
        app_history.bump("app2.desktop")
        assert app_history.get_top_app_ids() == ["app2.desktop", "app1.desktop"]
