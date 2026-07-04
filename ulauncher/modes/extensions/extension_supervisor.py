from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ulauncher.modes.extensions.extension_controller import PreviewExtensionController
    from ulauncher.modes.extensions.extension_runtime import ExtensionRuntime


class ExtensionSupervisor:
    """Holds the extension processes owned by this process.

    Only the app process claims ownership and may spawn extension processes. Other processes
    importing this module (the CLI) see it empty and unclaimed: previews and running extensions
    live in the app, and the CLI asks the app to reconcile via D-Bus events
    ("extensions:reload", "extensions:stop", ...).
    """

    runtimes: dict[str, ExtensionRuntime]
    stopped_listeners: dict[str, list[Callable[[], None]]]
    _preview: PreviewExtensionController | None
    is_owner: bool

    def __init__(self) -> None:
        self.runtimes = {}
        self.stopped_listeners = defaultdict(list)
        self._preview = None
        self.is_owner = False

    def claim_ownership(self) -> None:
        self.is_owner = True

    def get_preview(self, ext_id: str | None = None) -> PreviewExtensionController | None:
        """The active preview, or None. When `ext_id` is given, return it only if it targets that extension."""
        if self._preview and (ext_id is None or self._preview.id == ext_id):
            return self._preview
        return None

    def set_preview(self, ext_id: str, path: str, with_debugger: bool = False) -> None:
        from ulauncher.modes.extensions.extension_controller import PreviewExtensionController

        self._preview = PreviewExtensionController(ext_id=ext_id, path=path, with_debugger=with_debugger)

    def clear_preview(self) -> None:
        self._preview = None


supervisor = ExtensionSupervisor()
