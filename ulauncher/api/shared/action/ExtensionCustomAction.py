from __future__ import annotations  # noqa: N999

from typing import Any

from ulauncher.api._deprecation import warn_legacy_api
from ulauncher.api._utils import legacy_custom_data_store
from ulauncher.internals.effects import EffectType


def ExtensionCustomAction(data: Any, keep_app_open: bool = False) -> dict[str, Any]:  # noqa: N802
    """
    This effect is used to pass custom data back to the extension when the result item is activated.
    """
    warn_legacy_api(
        "ExtensionCustomAction",
        "Define `actions` on your `Result` and handle them in the extension's `on_result_activation` method instead.",
    )
    ref = id(data)
    legacy_custom_data_store[ref] = data
    return {"type": EffectType.LEGACY_ACTIVATE_CUSTOM, "ref": ref, "keep_app_open": keep_app_open}
