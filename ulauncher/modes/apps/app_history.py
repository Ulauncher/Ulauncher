from __future__ import annotations

from ulauncher import paths
from ulauncher.utils.json_conf import JsonKeyValueConf

_app_history_path = f"{paths.STATE}/app_starts.json"


class _AppHistory(JsonKeyValueConf[str, int]):
    def get_app_ranking(self) -> list[str]:
        """Get list of app IDs sorted by launch count"""
        return sorted(self, key=lambda k: self.get(k, 0), reverse=True)

    def bump(self, app_id: str) -> None:
        self[app_id] = self.get(app_id, 0) + 1
        self.save()


app_history = _AppHistory.load(_app_history_path)
