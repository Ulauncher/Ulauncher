from __future__ import annotations


def CopyToClipboardAction(text: str) -> dict[str, str]:
    return {"type": "action:clipboard_store", "data": text}
