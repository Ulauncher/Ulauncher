from __future__ import annotations

from typing import Any


def Copy(text: str) -> dict[str, str]:
    return {"type": "action:clipboard_store", "data": text}


def Open(item: str) -> dict[str, str]:
    return {"type": "action:open", "data": item}


def RunScript(script: str, args: str = "") -> dict[str, str | list[str]]:
    return {"type": "action:legacy_run_script", "data": [script, args]}


def ActionList(actions: list[Any]) -> dict[str, Any]:
    return {"type": "action:legacy_run_many", "data": actions}
