from __future__ import annotations

import contextlib
import logging
import operator
import time
from os.path import basename
from typing import TypedDict

from ulauncher import paths
from ulauncher.gi import GioUnix
from ulauncher.internals.result import Result
from ulauncher.utils.json_utils import json_load, json_save

logger = logging.getLogger()
app_starts_path = f"{paths.STATE}/app_starts.json"

class AppStartData(TypedDict):
    count: int
    last_launches: list[float]

_raw_app_starts = json_load(app_starts_path)
app_starts: dict[str, AppStartData] = {}
for _app_id, _data in _raw_app_starts.items():
    if isinstance(_data, int):
        app_starts[_app_id] = {"count": _data, "last_launches": []}
    elif isinstance(_data, dict):
        app_starts[_app_id] = {"count": _data.get("count", 0), "last_launches": _data.get("last_launches", [])}


class AppResult(Result):
    searchable = True
    app_id = ""
    _executable = ""
    actions = {"launch": {"name": "Launch application", "icon": "system-run"}}

    def __init__(self, app_info: GioUnix.DesktopAppInfo) -> None:
        super().__init__(
            name=app_info.get_display_name(),
            icon=app_info.get_string("Icon") or "",
            description=app_info.get_description() or app_info.get_generic_name() or "",
            keywords=app_info.get_keywords(),
            app_id=app_info.get_id(),
            # TryExec is what we actually want (name of/path to exec), but it's often not specified
            # get_executable uses Exec, which is always specified, but it will return the actual executable.
            # Sometimes the actual executable is not the app to start, but a wrappers like "env" or "sh -c"
            _executable=basename(app_info.get_string("TryExec") or app_info.get_executable() or ""),
        )

    @staticmethod
    def from_id(app_id: str) -> AppResult | None:
        # Suppress errors due to app being uninstalled/not found
        with contextlib.suppress(TypeError):
            if app_info := GioUnix.DesktopAppInfo.new(app_id):
                return AppResult(app_info)
        return None

    @staticmethod
    def get_top_app_ids() -> list[str]:
        scores = {app_id: AppResult._calculate_score(data) for app_id, data in app_starts.items()}
        sorted_ids = sorted(scores.items(), key=operator.itemgetter(1), reverse=True)
        return [app_id for app_id, score in sorted_ids]

    @staticmethod
    def _calculate_score(data: AppStartData) -> float:
        now = time.time()
        score = data["count"] * 0.1
        for launch_time in data["last_launches"]:
            diff = now - launch_time
            if diff < 86400:
                score += 100
            elif diff < 259200:
                score += 80
            elif diff < 604800:
                score += 60
            elif diff < 1209600:
                score += 40
            elif diff < 2592000:
                score += 20
            else:
                score += 10
        return score

    def get_searchable_fields(self) -> list[tuple[str, float]]:
        frequency_weight = 1.0
        sorted_app_ids = AppResult.get_top_app_ids()
        if count := len(sorted_app_ids):
            index = sorted_app_ids.index(self.app_id) if self.app_id in sorted_app_ids else count
            frequency_weight = 1.0 - (index / count * 0.1) + 0.05

        return [
            (self.name, 1 * frequency_weight),
            (self._executable, 0.8 * frequency_weight),  # command names, such as "baobab" or "nautilus"
            (self.description, 0.7 * frequency_weight),
            *[(k, 0.6 * frequency_weight) for k in self.keywords],
        ]

    def bump_starts(self) -> None:
        data = app_starts.get(self.app_id, {"count": 0, "last_launches": []})
        data["count"] += 1
        data["last_launches"].append(time.time())
        if len(data["last_launches"]) > 10:
            data["last_launches"].pop(0)

        app_starts[self.app_id] = data
        json_save(app_starts, app_starts_path)
