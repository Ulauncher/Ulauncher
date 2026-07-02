from __future__ import annotations

import logging
from typing import Iterator

from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.modes.extensions.extension_supervisor import supervisor
from ulauncher.utils.eventbus import EventBus

events = EventBus("extension_lifecycle")

logger = logging.getLogger(__name__)


def _get_preview_controller() -> ExtensionController | None:
    preview = supervisor.preview
    if preview.ext_id:
        return ExtensionController(preview.ext_id, preview.path)
    return None


def get(ext_id: str, include_preview: bool = True) -> ExtensionController | None:
    if include_preview and ext_id == supervisor.preview.ext_id and (preview_ext := _get_preview_controller()):
        return preview_ext
    path = extension_finder.locate(ext_id)
    return ExtensionController(ext_id, path) if path else None


def iterate(sort: bool = False, include_preview: bool = True) -> Iterator[ExtensionController]:
    controllers = {ext_id: ExtensionController(ext_id, path) for ext_id, path in extension_finder.iterate()}
    if include_preview and (preview_controller := _get_preview_controller()):
        controllers[preview_controller.id] = preview_controller

    if not sort:
        yield from controllers.values()
        return

    def sort_key(controller: ExtensionController) -> int:
        if controller.is_preview:
            return 0
        if controller.has_error:
            return 2
        if not controller.is_enabled:
            return 3
        return 1

    yield from sorted(controllers.values(), key=sort_key)


@events.on
def removed(ext_id: str) -> None:
    """Handle removal events dispatched by controllers."""
    # A still-locatable extension after removal is a non-manageable copy (e.g. distro-packaged).
    # Disable it rather than let it silently take over the removed extension's id.
    fallback_path = extension_finder.locate(ext_id)
    if fallback_path:
        fallback_controller = ExtensionController(ext_id, fallback_path)
        # TODO: Try to avoid accessing state attribute (we could call toggle_enabled() instead, but that's async)
        fallback_controller.state.save(is_enabled=False)
        logger.info(
            "Non-manageable extension with the same id exists in '%s'. It was kept disabled.",
            fallback_path,
        )
