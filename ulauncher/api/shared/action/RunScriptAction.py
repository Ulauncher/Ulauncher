def RunScriptAction(script: str, args=""):
    return {"type": "action:legacy_run_script", "data": [script, args]}
