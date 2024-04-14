from __future__ import annotations


def RunScriptAction(script: str, args: str = "") -> dict[str, str | list[str]]:
    return {"type": "action:legacy_run_script", "data": [script, args]}
