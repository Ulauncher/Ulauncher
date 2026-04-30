from __future__ import annotations

from ulauncher import paths
from ulauncher.utils.json_conf import JsonKeyValueConf

app_starts_path = f"{paths.STATE}/app_starts.json"


class AppStarts(JsonKeyValueConf[str, int]):
    _top_ids: list[str] | None = None

    def get_top_app_ids(self) -> list[str]:
        if self._top_ids is None:
            self._top_ids = sorted(self, key=lambda k: self.get(k, 0), reverse=True)
        return self._top_ids

    def bump(self, app_id: str) -> None:
        self._top_ids = None
        self[app_id] = self.get(app_id, 0) + 1
        self.save()


app_starts = AppStarts.load(app_starts_path)
