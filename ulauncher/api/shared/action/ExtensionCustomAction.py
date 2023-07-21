from __future__ import annotations

from typing import Any

# This holds references to custom data for use with ExtensionCustomAction
# This way the data never travels to the Ulauncher app and back. Only a reference to it.
# So the data can be anything, even if the serialization doesn't handle it
custom_data_store: dict[int, Any] = {}


def ExtensionCustomAction(data, keep_app_open=False):
    ref = id(data)
    custom_data_store[ref] = data
    return {"type": "event:activate_custom", "ref": ref, "keep_app_open": keep_app_open}
