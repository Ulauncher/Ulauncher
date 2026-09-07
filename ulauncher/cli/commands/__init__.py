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


def _install_arg_id(input_arg: str) -> str:
    """Normalize the argument and derive its repo id, falling back on the input as-is."""
    from ulauncher.data import Ok
    from ulauncher.internals.install_source import parse_repo_url

    arg = normalize_install_arg(input_arg)
    if isinstance(parse_result := parse_repo_url(arg), Ok):
        return parse_result.value.repo_id
    return arg


def get_ext_record(input_arg: str) -> ExtensionRecord | None:
    """Returns an ExtensionRecord instance if the argument matches an installed extension, otherwise None."""
    return get_ext_registry().get(_install_arg_id(input_arg))


def get_theme_id(input_arg: str) -> str | None:
    """Resolve an argument to an installed theme's repo id, or None if no installed theme matches."""
    from ulauncher.internals import theme_installer

    arg = _install_arg_id(input_arg)
    return arg if arg in theme_installer.installed_ids() else None


def normalize_install_arg(path: str) -> str:
    if "://" in path:
        return path
    with contextlib.suppress(OSError):
        return str(Path(path).resolve(strict=True))
    return path
