from __future__ import annotations

from typing import Any


def ActionList(actions: list[Any]) -> dict[str, Any]:
    return {"type": "action:legacy_run_many", "data": actions}
