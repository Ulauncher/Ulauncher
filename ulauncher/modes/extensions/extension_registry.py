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

    def sort_key(controller: ExtensionController) -> int:
        if controller.is_preview:
            return 0  # preview first
        if controller.is_running:
            return 1  # running second
        return 2  # stopped and errored last

    yield from sorted(_ext_controllers.values(), key=sort_key)


def load(ext_id: str, path: str | None = None) -> ExtensionController:
    """Load an extension controller into the registry without starting it."""
    if not path:
        path = extension_finder.locate(ext_id)
        if not path:
            # Remove extension from registry if it can no longer be found
            # This can happen when an extension is deleted via the CLI or manually,
            # in which case the in-memory registry should reflect that
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

    # If extension still exists after being removed, it means it's a non-manageable extension
    # Set its state to disabled instead of completely removing it
    fallback_path = extension_finder.locate(ext_id)
    if fallback_path:
        fallback_controller = ExtensionController(ext_id, fallback_path)
        # TODO: Try to avoid accessing state attribute (we could call toggle_enabled() instead, but that's async)
        fallback_controller.state.save(is_enabled=False)
        _ext_controllers[ext_id] = fallback_controller
        logger.info(
            "Non-manageable extension with the same id exists in '%s'. It was kept disabled.",
            fallback_path,
        )
