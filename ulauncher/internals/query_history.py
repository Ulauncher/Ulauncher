from __future__ import annotations

from ulauncher import paths
from ulauncher.data import JsonKeyValueConf

_QUERY_HISTORY_PATH = f"{paths.STATE}/query_history.json"


class QueryHistory(JsonKeyValueConf[str, str]):
    @classmethod
    def load(cls) -> QueryHistory:  # type: ignore[override]
        return super().load(_QUERY_HISTORY_PATH)
