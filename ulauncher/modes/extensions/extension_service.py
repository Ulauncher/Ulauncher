from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from threading import Thread
from typing import TYPE_CHECKING, Callable, Literal

from ulauncher.utils import scheduling
from ulauncher.utils.eventbus import EventBus

if TYPE_CHECKING:
    from ulauncher.modes.extensions.extension_controller import ExtensionController, PreviewExtensionController
    from ulauncher.modes.extensions.extension_runtime import ExtensionRuntime

logger = logging.getLogger(__name__)
events = EventBus("extensions", skip_if_not_bound=True)


class ExtensionService:
    """Owns the extension processes and handles the extension lifecycle intents.

    Only the app process activates the service and may spawn extension processes. Other processes
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

    def activate(self) -> None:
        """Claim extension process ownership, bind the lifecycle event handlers and start the
        enabled extensions. Called by ExtensionMode when the app loads its modes."""
        self.is_owner = True
        events.set_self(self)
        scheduling.run_when_idle(self._start_extensions)

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

    def _start_extensions(self) -> None:
        # Imported here to break the import cycle (extension_registry -> extension_controller -> here)
        from ulauncher.modes.extensions import extension_registry

        for ext in extension_registry.iterate():
            if ext.state.is_enabled:
                ext.start()

    def _run_batch_job(
        self,
        extension_ids: list[str],
        jobs: list[Literal["start", "stop"]],
        callback: Callable[[], None] | None = None,
    ) -> None:
        from ulauncher.modes.extensions import extension_registry

        ext_controllers: list[ExtensionController] = []
        for ext_id in extension_ids:
            if ext := extension_registry.get(ext_id):
                ext_controllers.append(ext)  # noqa: PERF401

        # run the reload in a separate thread to avoid blocking the main thread
        async def run_batch_async() -> None:
            for job in jobs:
                if job == "start":
                    for controller in ext_controllers:
                        if controller.is_enabled:
                            controller.start()
                elif job == "stop":
                    await asyncio.gather(*[c.stop() for c in ext_controllers])

        def run_batch() -> None:
            asyncio.run(run_batch_async())
            if callback:
                callback()

        Thread(target=run_batch).start()

    @events.on
    def reload(
        self,
        extension_ids: list[str] | None = None,
    ) -> None:
        if not extension_ids:
            logger.warning("Reload message received without any extension IDs. No extensions will be restarted.")
            return

        logger.info("Reloading extension(s): %s", ", ".join(extension_ids))

        self._run_batch_job(
            extension_ids,
            ["stop", "start"],
            callback=lambda: logger.info("%s extensions (re)loaded", len(extension_ids)),
        )

    @events.on
    def stop(self, extension_ids: list[str] | None = None) -> None:
        if not extension_ids:
            logger.warning("Stop message received without any extension IDs. No extensions will be stopped.")
            return

        logger.info("Stopping extension(s): %s", ", ".join(extension_ids))

        self._run_batch_job(
            extension_ids, ["stop"], callback=lambda: logger.info("%s extensions stopped", len(extension_ids))
        )

    @events.on
    def preview_ext(self, ext_id: str, path: str, with_debugger: bool = False) -> None:
        """Run an extension from a dev path WITHOUT installing it. Triggered from the CLI via D-Bus.

        While the preview is active, the controller with this id launches from the dev path; its
        dependencies are installed by the CLI before this is called.
        """

        logger.info("[preview] Previewing ext_id=%s path=%s debugger=%s", ext_id, path, with_debugger)
        self.set_preview(ext_id, path, with_debugger)

        # Guard the restart against a stop_preview that races in during the stop: only relaunch if
        # this preview is still the active one, otherwise stop_preview owns restoring the extension.
        def start_if_still_previewing() -> None:
            if self.get_preview(ext_id):
                self._run_batch_job([ext_id], ["start"])

        # Relaunch from the dev path, stopping any conflicting installed instances
        self._run_batch_job([ext_id], ["stop"], callback=start_if_still_previewing)

    @events.on
    def stop_preview(self) -> None:
        """Stop the active preview and restore the installed extension. Triggered from the CLI via D-Bus"""
        from ulauncher.modes.extensions import extension_registry

        preview_ext = self.get_preview()
        if not preview_ext:
            # will happen if preview is interrupted before started
            logger.debug("[preview] Ignoring stop_preview; no preview active")
            return

        logger.info("[preview] Stopping preview %s", preview_ext.id)

        def restore_original() -> None:
            self.clear_preview()
            # Reload from the installed path, or drop the controller if the extension was never installed.
            controller = extension_registry.get(preview_ext.id)
            if controller and controller.is_enabled:
                self._run_batch_job([preview_ext.id], ["start"])

        self._run_batch_job([preview_ext.id], ["stop"], callback=restore_original)


ext_service = ExtensionService()
