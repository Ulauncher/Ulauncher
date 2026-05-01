from __future__ import annotations

from ulauncher import paths
from ulauncher.utils.json_conf import JsonKeyValueConf

app_starts_path = f"{paths.STATE}/app_starts.json"


class AppStarts(JsonKeyValueConf[str, int]):
    def get_top_app_ids(self) -> list[str]:
        return sorted(self, key=lambda k: self.get(k, 0), reverse=True)

    def bump(self, app_id: str) -> None:
        self[app_id] = self.get(app_id, 0) + 1
        self.save()


app_starts = AppStarts.load(app_starts_path)
