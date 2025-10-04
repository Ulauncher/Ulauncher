from __future__ import annotations

import logging
from typing import Iterator

from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.extension_controller import (
    ExtensionController,
    ExtensionNotFoundError,
    lifecycle_events,
)
from ulauncher.utils.singleton import Singleton

logger = logging.getLogger()


class ExtensionRegistry(metaclass=Singleton):
    """Central in-memory registry for extension controllers."""

    _registry: dict[str, ExtensionController]

    def __init__(self) -> None:
        self._registry = {}
        lifecycle_events.set_self(self)

    def get(self, ext_id: str) -> ExtensionController | None:
        """Get an extension from the registry."""
        return self._registry.get(ext_id)

    def get_or_raise(self, ext_id: str) -> ExtensionController:
        """Get an extension from the registry or raise if not found."""
        controller = self._registry.get(ext_id)
        if not controller:
            msg = f"Extension with ID '{ext_id}' not found in registry"
            raise ExtensionNotFoundError(msg)

        return controller

    def iterate(self) -> Iterator[ExtensionController]:
        """Iterate over registered extension controllers."""
        yield from self._registry.values()

    def load(self, ext_id: str, path: str | None = None) -> ExtensionController:
        """Load an extension controller into the registry without starting it."""
        if not path:
            path = extension_finder.locate(ext_id)
            if not path:
                self._registry.pop(ext_id, None)
                msg = f"Extension with ID '{ext_id}' not found"
                raise ExtensionNotFoundError(msg)

        controller = ExtensionController(ext_id, path)
        self._registry[ext_id] = controller
        return controller

    def load_all(self) -> Iterator[ExtensionController]:
        """Load all extensions found by the extension finder into the registry."""
        for ext_id, ext_path in extension_finder.iterate():
            self.load(ext_id, ext_path)

        yield from self._registry.values()

    @lifecycle_events.on
    def installed(self, controller: ExtensionController) -> None:
        """Handle install events dispatched by controllers."""
        self._registry[controller.id] = controller

    @lifecycle_events.on
    def updated(self, controller: ExtensionController) -> None:
        """Handle update events dispatched by controllers."""
        self._registry[controller.id] = controller

    @lifecycle_events.on
    def removed(self, ext_id: str) -> None:
        """Handle removal events dispatched by controllers."""
        self._registry.pop(ext_id, None)


# Instantiate singleton early so event handlers are bound when first emitted
ExtensionRegistry()
