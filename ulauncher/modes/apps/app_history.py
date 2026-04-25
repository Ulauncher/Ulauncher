from __future__ import annotations

import operator
import time
from typing import Any

from ulauncher import paths
from ulauncher.utils.base_data_class import BaseDataClass
from ulauncher.utils.json_conf import JsonKeyValueConf

_APP_HISTORY_PATH = f"{paths.STATE}/app_starts.json"
_MAX_APP_HISTORY = 10


class _AppHistoryData(BaseDataClass):
    count = 0
    last_launches: list[float] = []


class _AppHistory(JsonKeyValueConf[str, _AppHistoryData]):
    _ranking_cache: list[str] | None = None

    def _coerce_value(self, value: Any) -> _AppHistoryData:
        if isinstance(value, _AppHistoryData):
            return value
        valid_count = 0
        valid_launches: list[float] = []

        if isinstance(value, int):
            valid_count = value
        elif isinstance(value, dict):
            raw_count = value.get("count")
            if isinstance(raw_count, int):
                valid_count = raw_count
            elif isinstance(raw_count, str) and raw_count.isdigit():
                valid_count = int(raw_count)

            raw_launches = value.get("last_launches")
            if isinstance(raw_launches, (list, tuple)):
                valid_launches = [float(x) for x in raw_launches if isinstance(x, (int, float))][-_MAX_APP_HISTORY:]

        return _AppHistoryData(count=valid_count, last_launches=valid_launches)

    def get_app_ranking(self) -> list[str]:
        if self._ranking_cache is None:
            scores = {app_id: _AppHistory._calculate_score(data) for app_id, data in self.items()}
            sorted_ids = sorted(scores.items(), key=operator.itemgetter(1), reverse=True)
            self._ranking_cache = [app_id for app_id, score in sorted_ids]
        return self._ranking_cache

    def clear_ranking_cache(self) -> None:
        self._ranking_cache = None

    @staticmethod
    def _calculate_score(data: _AppHistoryData) -> float:
        now = time.time()
        score = data.count * 0.1
        for launch_time in data.last_launches:
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

    def bump(self, app_id: str) -> None:
        data = self.get(app_id)
        if not data:
            data = _AppHistoryData()
            self[app_id] = data

        data.count += 1
        data.last_launches.append(time.time())
        if len(data.last_launches) > _MAX_APP_HISTORY:
            data.last_launches.pop(0)

        self.clear_ranking_cache()
        self.save()


app_history = _AppHistory.load(_APP_HISTORY_PATH)
