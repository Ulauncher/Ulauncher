from __future__ import annotations  # noqa: N999

from typing import Any

# This holds references to custom data for use with ExtensionCustomAction
# This way the data never travels to the Ulauncher app and back. Only a reference to it.
# So the data can be anything, even if the serialization doesn't handle it
custom_data_store: dict[int, Any] = {}


def ExtensionCustomAction(data: Any, keep_app_open: bool = False) -> dict[str, Any]:  # noqa: N802
    """
    This action is used to pass custom data back to the extension when the result item is activated.
    """
    ref = id(data)
    custom_data_store[ref] = data
    return {"type": "action:activate_custom", "ref": ref, "keep_app_open": keep_app_open}
