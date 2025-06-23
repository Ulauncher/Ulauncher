# ruff: noqa: UP006, UP007

from typing import Any, Dict, List, TypeAlias, Union  # type: ignore[attr-defined]

from ulauncher.internals.result import Result

"""
ActionMetadata describes the action to be performed by the Ulauncher app.
It can be a dict with any value that can be serialized to JSON.
"""
ActionMetadata: TypeAlias = Union[List[Result], Dict[str, Any], bool, str]
