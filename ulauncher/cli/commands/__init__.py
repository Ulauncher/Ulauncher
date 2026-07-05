from __future__ import annotations

import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from ulauncher.utils.lru_cache import lru_cache

if TYPE_CHECKING:
    from ulauncher.modes.extensions.extension_record import ExtensionRecord
    from ulauncher.modes.extensions.extension_registry import ExtensionRegistry


@lru_cache
def get_ext_registry() -> ExtensionRegistry:
    from ulauncher.modes.extensions.extension_registry import ExtensionRegistry

    return ExtensionRegistry()


def get_ext_record(input_arg: str) -> ExtensionRecord | None:
    """Parses the input argument and returns an ExtensionRecord instance if it's installed, otherwise None."""
    from ulauncher.modes.extensions.extension_remote import parse_extension_url

    arg = normalize_ext_arg(input_arg)
    with contextlib.suppress(ValueError):
        parse_result = parse_extension_url(arg)
        arg = parse_result.ext_id

    return get_ext_registry().get(arg)


def normalize_ext_arg(path: str) -> str:
    if "://" in path:
        return path
    with contextlib.suppress(OSError):
        return str(Path(path).resolve(strict=True))
    return path
