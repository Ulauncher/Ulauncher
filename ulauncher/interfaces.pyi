from typing import Any

from typing_extensions import TypeAlias

from ulauncher.internals.result import Result

"""
ActionMetadata describes the action to be performed by the Ulauncher app.
It can be a dict with any value that can be serialized to JSON.
"""
ActionMetadata: TypeAlias = list[Result] | dict[str, Any] | bool | str
