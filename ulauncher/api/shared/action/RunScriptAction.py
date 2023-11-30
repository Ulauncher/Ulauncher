def RunScriptAction(script: str, args=""):  # type: ignore[no-untyped-def]
    return {"type": "action:legacy_run_script", "data": [script, args]}
