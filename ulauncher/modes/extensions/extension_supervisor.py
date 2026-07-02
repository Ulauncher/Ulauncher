from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ulauncher.modes.extensions.extension_runtime import ExtensionRuntime


class PreviewExtension:
    """The single extension currently being previewed from a dev path via the CLI, if any.

    Only one runs at a time (the debugger binds a fixed port). While active, the controller whose id
    matches launches from `path` (with `with_debugger`) instead of its installed location.
    """

    ext_id: str | None = None
    path: str = ""
    with_debugger: bool = False

    def set(self, ext_id: str, path: str, with_debugger: bool) -> None:
        self.ext_id = ext_id
        self.path = path
        self.with_debugger = with_debugger

    def clear(self) -> None:
        self.ext_id = None
        self.path = ""
        self.with_debugger = False


class ExtensionSupervisor:
    """Holds the extension processes owned by this process.

    Only the app process claims ownership and may spawn extension processes. Other processes
    importing this module (the CLI) see it empty and unclaimed: previews and running extensions
    live in the app, and the CLI asks the app to reconcile via D-Bus events
    ("extensions:reload", "extensions:stop", ...).
    """

    runtimes: dict[str, ExtensionRuntime]
    stopped_listeners: dict[str, list[Callable[[], None]]]
    preview: PreviewExtension
    is_owner: bool

    def __init__(self) -> None:
        self.runtimes = {}
        self.stopped_listeners = defaultdict(list)
        self.preview = PreviewExtension()
        self.is_owner = False

    def claim_ownership(self) -> None:
        self.is_owner = True


supervisor = ExtensionSupervisor()
