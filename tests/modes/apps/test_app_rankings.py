from __future__ import annotations

from ulauncher.modes.apps.app_rankings import AppRankings as _AppRankings


class AppRankings(_AppRankings):
    def save(self) -> bool:
        return False


class TestAppRankings:
    def test_get_app_ids_sorted_by_score(self) -> None:
        app_rankings = AppRankings({"a.desktop": 2.0, "b.desktop": 5.0, "c.desktop": 1.0})
        assert app_rankings.get_app_ids() == ["b.desktop", "a.desktop", "c.desktop"]

    def test_bump_increases_relative_score(self) -> None:
        app_rankings = AppRankings({"app1.desktop": 10.0, "app2.desktop": 10.0})
        app_rankings.bump("app2.desktop")
        assert app_rankings["app2.desktop"] > app_rankings["app1.desktop"]

    def test_bump_updates_top_app_ids(self) -> None:
        app_rankings = AppRankings({"app1.desktop": 1.0, "app2.desktop": 1.0})
        app_rankings.bump("app2.desktop")
        assert app_rankings.get_app_ids() == ["app2.desktop", "app1.desktop"]

    def test_decay_adapts_to_history(self) -> None:
        light_use = 2.0
        light = AppRankings({"a.desktop": light_use})
        light.bump("b.desktop")
        light_retention_ratio = light["a.desktop"] / light_use

        heavy_use = 2048.0
        heavy = AppRankings({"a.desktop": heavy_use})
        heavy.bump("b.desktop")
        heavy_retention_ratio = heavy["a.desktop"] / heavy_use

        # light history should be more volatile per launch
        assert heavy_retention_ratio > light_retention_ratio
