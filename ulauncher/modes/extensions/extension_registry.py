from __future__ import annotations

import logging
from typing import Iterator

from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.extension_controller import ExtensionController, preview
from ulauncher.utils.eventbus import EventBus

events = EventBus("extension_lifecycle")

logger = logging.getLogger(__name__)
_ext_controllers: dict[str, ExtensionController] = {}


def _get_preview_controller() -> ExtensionController | None:
    if preview.ext_id:
        return ExtensionController(preview.ext_id, preview.path)
    return None


def get(ext_id: str) -> ExtensionController | None:
    if ext_id == preview.ext_id and (preview_ext := _get_preview_controller()):
        return preview_ext
    return _ext_controllers.get(ext_id)


def iterate() -> Iterator[ExtensionController]:
    """Iterate over registered extension controllers."""

    def sort_key(controller: ExtensionController) -> int:
        if controller.is_preview:
            return 0  # preview (first)
        if controller.has_error:
            return 3
        if not controller.is_enabled:
            return 4
        if not controller.is_running:
            return 2
        return 1  # running

    controllers = dict(_ext_controllers)
    if preview_controller := _get_preview_controller():
        controllers[preview_controller.id] = preview_controller

    yield from sorted(controllers.values(), key=sort_key)


def load(ext_id: str, path: str | None = None) -> ExtensionController | None:
    """Load an extension controller into the registry without starting it."""
    if not path:
        path = extension_finder.locate(ext_id)
        if not path:
            # Remove extension from registry if it can no longer be found
            # This can happen when an extension is deleted via the CLI or manually,
            # in which case the in-memory registry should reflect that
            _ext_controllers.pop(ext_id, None)
            return None

    controller = ExtensionController(ext_id, path)
    _ext_controllers[ext_id] = controller
    return controller


def load_all() -> list[ExtensionController]:
    """Load all extensions found by the extension finder into the registry."""
    for ext_id, ext_path in extension_finder.iterate():
        load(ext_id, ext_path)

    return list(_ext_controllers.values())


@events.on
def installed(controller: ExtensionController) -> None:
    """Handle install events dispatched by controllers."""
    _ext_controllers[controller.id] = controller


@events.on
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
