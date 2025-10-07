from __future__ import annotations

import logging
from typing import Iterator

from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.extension_controller import (
    ExtensionController,
    ExtensionNotFoundError,
    lifecycle_events,
)

logger = logging.getLogger()
_ext_controllers: dict[str, ExtensionController] = {}


def get(ext_id: str) -> ExtensionController:
    """Get an extension from the registry or raise if not found."""
    controller = _ext_controllers.get(ext_id)
    if not controller:
        msg = f"Extension with ID '{ext_id}' not found in registry"
        raise ExtensionNotFoundError(msg)

    return controller


def iterate() -> Iterator[ExtensionController]:
    """Iterate over registered extension controllers."""
    yield from _ext_controllers.values()


def load(ext_id: str, path: str | None = None) -> ExtensionController:
    """Load an extension controller into the registry without starting it."""
    if not path:
        path = extension_finder.locate(ext_id)
        if not path:
            _ext_controllers.pop(ext_id, None)
            msg = f"Extension with ID '{ext_id}' not found"
            raise ExtensionNotFoundError(msg)

    controller = ExtensionController(ext_id, path)
    _ext_controllers[ext_id] = controller
    return controller


def load_all() -> Iterator[ExtensionController]:
    """Load all extensions found by the extension finder into the registry."""
    for ext_id, ext_path in extension_finder.iterate():
        load(ext_id, ext_path)

    yield from _ext_controllers.values()


@lifecycle_events.on
def installed(controller: ExtensionController) -> None:
    """Handle install events dispatched by controllers."""
    _ext_controllers[controller.id] = controller


@lifecycle_events.on
def removed(ext_id: str) -> None:
    """Handle removal events dispatched by controllers."""
    _ext_controllers.pop(ext_id, None)
