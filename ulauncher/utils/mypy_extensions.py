"""
mypy_extensions cannot be installed via apt or dnf so we need to make sure TypedDict exists at runtime
"""

# pylint: disable=unused-import
from typing import Any, Callable, Dict  # noqa: F401


def _TypedDict(*args, **kw):
    pass


try:
    from mypy_extensions import TypedDict
except ImportError:
    TypedDict = _TypedDict
