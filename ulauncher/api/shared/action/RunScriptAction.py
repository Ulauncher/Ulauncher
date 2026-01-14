from ulauncher.internals import effects  # noqa: N999


def RunScriptAction(script: str, arg: str = "") -> effects.LegacyRunScript:  # noqa: N802
    if not isinstance(script, str):
        msg = f'Script argument "{script}" is invalid. It must be a string'
        raise TypeError(msg)
    if not script:
        msg = "Script argument cannot be empty"
        raise ValueError(msg)
    return {"type": effects.EffectType.LEGACY_RUN_SCRIPT, "data": [script, arg]}
