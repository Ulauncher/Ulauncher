from __future__ import annotations


def OpenAction(item: str) -> dict[str, str]:
    return {"type": "action:open", "data": item}
