from __future__ import annotations

import contextlib
from pathlib import Path
from typing import TYPE_CHECKING, Callable, TypeVar

from ulauncher.utils.lru_cache import lru_cache

if TYPE_CHECKING:
    from ulauncher.modes.extensions.extension_record import ExtensionRecord
    from ulauncher.modes.extensions.extension_registry import ExtensionRegistry
    from ulauncher.utils.subprocess_utils import OnError

T = TypeVar("T")


def run_blocking(start: Callable[[Callable[[T], None], OnError], None]) -> T:
    """Run a main loop until start's operation reports back, then return its value or raise its error."""
    from ulauncher.gi import GLib

    loop = GLib.MainLoop()
    result: list[T] = []
    error: Exception | None = None
    completed = False

    def on_success(value: T) -> None:
        nonlocal completed
        if completed:
            return
        result.append(value)
        completed = True
        loop.quit()

    def on_error(err: Exception) -> None:
        nonlocal error, completed
        if completed:
            return
        error = err
        completed = True
        loop.quit()

    start(on_success, on_error)
    # start() can report back before the loop runs, and GLib does not treat that quit() as
    # pending, so entering the loop afterwards would hang.
    if not completed:
        loop.run()
    if error:
        raise error
    return result[0]


@lru_cache
def get_ext_registry() -> ExtensionRegistry:
    from ulauncher.modes.extensions.extension_registry import ExtensionRegistry

    return ExtensionRegistry()


def get_ext_record(input_arg: str) -> ExtensionRecord | None:
    """Parses the input argument and returns an ExtensionRecord instance if it's installed, otherwise None."""
    from ulauncher.data import Ok
    from ulauncher.modes.extensions.extension_remote import parse_extension_url

    arg = normalize_ext_arg(input_arg)
    parse_result = parse_extension_url(arg)
    if isinstance(parse_result, Ok):
        arg = parse_result.value.ext_id

    return get_ext_registry().get(arg)


def normalize_ext_arg(path: str) -> str:
    if "://" in path:
        return path
    with contextlib.suppress(OSError):
        return str(Path(path).resolve(strict=True))
    return path
