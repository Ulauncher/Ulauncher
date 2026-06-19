from __future__ import annotations  # noqa: N999

from ulauncher.internals import effects


def ActionList(effect_list: list[effects.EffectMessage]) -> effects.LegacyRunMany:  # noqa: N802
    """
    ActionList is deprecated but maintained for backward compatibility.

    It allows you to pass multiple legacy "actions" for sequential execution.

    Note: Legacy actions have been replaced by effects and utils as of Extension version 3 (Ulauncher 6.0).
    Effects are mutually exclusive, and combining them can lead to undefined behavior.
    When writing new extensions, please use effects and/or utils instead.

    :param list effect_list: List of effect messages
    """
    return {"type": effects.EffectType.LEGACY_RUN_MANY, "data": effect_list}
