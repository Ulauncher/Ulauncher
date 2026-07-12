from ulauncher.api._deprecation import warn_legacy_api  # noqa: N999
from ulauncher.internals import effects


def RunScriptAction(script: str, arg: str = "") -> effects.LegacyRunScript:  # noqa: N802
    warn_legacy_api("RunScriptAction", "Run the script yourself from the event handler (e.g. with `subprocess`).")
    if not isinstance(script, str):
        msg = f'Script argument "{script}" is invalid. It must be a string'
        raise TypeError(msg)
    if not script:
        msg = "Script argument cannot be empty"
        raise ValueError(msg)
    return {"type": effects.EffectType.LEGACY_RUN_SCRIPT, "args": [script, arg]}
