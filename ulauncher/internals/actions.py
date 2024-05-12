from __future__ import annotations

from typing import Any


def copy(text: str) -> dict[str, str]:
    return {"type": "action:clipboard_store", "data": text}


def open(item: str) -> dict[str, str]:  # noqa: A001
    return {"type": "action:open", "data": item}


def run_script(script: str, args: str = "") -> dict[str, str | list[str]]:
    return {"type": "action:legacy_run_script", "data": [script, args]}


def action_list(actions: list[Any]) -> dict[str, Any]:
    return {"type": "action:legacy_run_many", "data": actions}
