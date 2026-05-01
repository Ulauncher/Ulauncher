from __future__ import annotations

from ulauncher import paths
from ulauncher.utils.json_conf import JsonKeyValueConf

_APP_HISTORY_PATH = f"{paths.STATE}/app_starts.json"


class _AppHistory(JsonKeyValueConf[str, int]):
    _ranking_cache: list[str] | None = None

    def get_app_ranking(self) -> list[str]:
        """Get list of app IDs sorted by launch count"""
        if self._ranking_cache is None:
            self._ranking_cache = sorted(self, key=lambda k: self.get(k, 0), reverse=True)
        return self._ranking_cache

    def clear_ranking_cache(self) -> None:
        self._ranking_cache = None

    def bump(self, app_id: str) -> None:
        self[app_id] = self.get(app_id, 0) + 1
        self.clear_ranking_cache()
        self.save()


app_history = _AppHistory.load(_APP_HISTORY_PATH)
