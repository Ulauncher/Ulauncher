from __future__ import annotations  # noqa: N999

from ulauncher.api._deprecation import warn_legacy_api
from ulauncher.internals import effects


def ActionList(effect_list: list[effects.EffectMessage]) -> effects.LegacyRunMany:  # noqa: N802
    """
    Passes multiple legacy "actions" for sequential execution.

    :param list effect_list: List of effect messages
    """
    warn_legacy_api(
        "ActionList",
        "API v2 Actions including ActionList have been deprecated in favor of class methods "
        "`self.clipboard_store(...)` and `self.notify(...)` which can be called directly from Extension class methods, "
        "and mutually exclusive Effects which can be returned only once per method",
    )
    return {"type": effects.EffectType.LEGACY_RUN_MANY, "effects": effect_list}
