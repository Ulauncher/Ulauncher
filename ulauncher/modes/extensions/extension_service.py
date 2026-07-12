from __future__ import annotations

import asyncio
import json
import logging
import sys
from collections import defaultdict
from threading import Thread
from typing import TYPE_CHECKING, Any, Callable, Literal, Protocol

from ulauncher import cli, paths
from ulauncher.gi import GLib
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies
from ulauncher.modes.extensions.extension_record import ExtensionRecord, PreviewExtensionRecord
from ulauncher.modes.extensions.extension_registry import ExtensionRegistry
from ulauncher.modes.extensions.extension_runtime import DEBUGPY_HOST, DEBUGPY_PORT, ExtensionRuntime
from ulauncher.utils import scheduling
from ulauncher.utils.eventbus import EventBus

if TYPE_CHECKING:
    from ulauncher.internals import ipc

logger = logging.getLogger(__name__)
events = EventBus("extensions", skip_if_not_bound=True)


class ExtensionServiceListener(Protocol):
    """What the service reports back about the extensions it runs. Implemented by ExtensionMode,
    which registers itself via ExtensionService.activate."""

    def started(self, ext_id: str) -> None: ...

    def errored(self, ext_id: str) -> None: ...

    def invalidate_cache(self) -> None: ...

    def handle_message(self, ext_id: str, message: ipc.ExtensionMessage) -> None: ...


class ExtensionService(ExtensionRegistry):
    """The app's ExtensionRegistry: also owns the extension processes and handles lifecycle intents.

    Extensions only run in the app process, so only app code uses the service. The CLI does its
    disk work with a plain ExtensionRegistry and asks the app to reconcile the processes via
    D-Bus events ("extensions:reload", "extensions:stop", ...).
    """

    runtimes: dict[str, ExtensionRuntime]
    stopped_listeners: dict[str, list[Callable[[], None]]]
    listener: ExtensionServiceListener | None

    def __init__(self) -> None:
        super().__init__(lifecycle=self)
        self.runtimes = {}
        self.stopped_listeners = defaultdict(list)
        self.listener = None
        events.set_self(self)

    def activate(self, listener: ExtensionServiceListener) -> None:
        """
        Set the listener that lifecycle events report to, and start the enabled extensions.
        Called by ExtensionMode when the app loads its modes.
        """
        self.listener = listener
        scheduling.run_when_idle(self._start_extensions)

    def _start_extensions(self) -> None:
        for ext in self.iterate():
            if ext.state.is_enabled:
                self.start_extension(ext)

    def _run_batch_job(
        self,
        extension_ids: list[str],
        jobs: list[Literal["start", "stop"]],
        callback: Callable[[], None] | None = None,
    ) -> None:
        records: list[ExtensionRecord] = []
        for ext_id in extension_ids:
            if ext := self.get(ext_id):
                records.append(ext)  # noqa: PERF401

        # run the reload in a separate thread to avoid blocking the main thread
        async def run_batch_async() -> None:
            for job in jobs:
                if job == "start":
                    for record in records:
                        if record.is_enabled:
                            self.start_extension(record)
                elif job == "stop":
                    await asyncio.gather(*[self.stop_extension(record) for record in records])

        def run_batch() -> None:
            asyncio.run(run_batch_async())
            if callback:
                callback()

        Thread(target=run_batch).start()

    def is_running(self, record: ExtensionRecord) -> bool:
        return record.id in self.runtimes

    async def toggle_enabled(self, record: ExtensionRecord, enabled: bool) -> bool:
        record.state.save(is_enabled=enabled, error_type="", error_message="")
        if enabled:
            return self.start_extension(record)
        await self.stop_extension(record)
        return False

    def start_extension(self, record: ExtensionRecord) -> bool:
        """
        Starts the extension in a subprocess
        Returns True if the extension was already running or successfully started, False otherwise.
        """
        if self.is_running(record):
            return True  # if already started, count as successful

        def exit_handler(cause: str, error_msg: str) -> None:
            listeners = self.stopped_listeners.get(record.id, [])
            for stop_listener in listeners:
                stop_listener()

            listeners.clear()

            if listener := self.listener:
                listener.invalidate_cache()

            if cause != "Stopped":
                logger.error('Extension "%s" exited with an error: %s (%s)', record.id, error_msg, cause)
                self.runtimes.pop(record.id, None)
                # A failing preview must not disable the installed extension by persisting its error.
                if not record.is_preview:
                    record.state.save(error_type=cause, error_message=error_msg)

                if listener := self.listener:
                    listener.errored(record.id)

        def message_handler(message: ipc.ExtensionMessage) -> None:
            if listener := self.listener:
                listener.handle_message(record.id, message)

        try:
            record.manifest.validate()
            record.manifest.check_compatibility(verbose=True)
        except ext_exceptions.ManifestError as err:
            exit_handler("Invalid", str(err))
            return False
        except ext_exceptions.CompatibilityError as err:
            exit_handler("Incompatible", str(err))
            return False

        if not record.is_preview:
            record.state.save(error_type="", error_message="")  # clear any previous error

        ext_deps = ExtensionDependencies(record.id, record.path)
        extension_main = f"{record.path}/main.py"
        cmd = [sys.executable, extension_main]

        if isinstance(record, PreviewExtensionRecord) and record.with_debugger:
            cmd = [
                sys.executable,
                "-m",
                "debugpy",
                "--listen",
                f"{DEBUGPY_HOST}:{DEBUGPY_PORT}",
                "--wait-for-client",
                extension_main,
            ]

        prefs = {p_id: pref.value for p_id, pref in record.preferences.items()}
        triggers = {t_id: t.default_keyword for t_id, t in record.manifest.triggers.items() if t.default_keyword}
        # backwards compatible v2 preferences format (with keywords added back)
        v2_prefs = {**triggers, **prefs}
        env = {
            "VERBOSE": str(int(cli.get_args().verbose)),
            "PYTHONPATH": ":".join(x for x in [paths.APPLICATION, ext_deps.get_dependencies_path()] if x),
            "EXTENSION_PREFERENCES": json.dumps(v2_prefs, separators=(",", ":")),
            "ULAUNCHER_EXTENSION_ID": record.id,
            "ULAUNCHER_INPUT_DEBOUNCE": str(record.manifest.input_debounce),
        }

        # socketpair/spawnv can fail for host-environment reasons (fd exhaustion, fork limits,
        # missing interpreter). Route these through exit_handler like a crash so the error is
        # surfaced consistently and any queued start listeners get cleaned up, rather than
        # raising out into callers.
        try:
            self.runtimes[record.id] = ExtensionRuntime(record.id, cmd, env, exit_handler, message_handler)
        except (OSError, GLib.Error) as err:
            exit_handler("FailedToStart", str(err))
            return False
        if listener := self.listener:
            listener.invalidate_cache()
            listener.started(record.id)
        return self.is_running(record)

    async def stop_extension(self, record: ExtensionRecord) -> None:
        """Stops the extension process if it is running."""
        if runtime := self.runtimes.pop(record.id, None):
            stopped_future: asyncio.Future[None] = asyncio.Future()
            self.stopped_listeners[record.id].append(lambda: stopped_future.set_result(None))
            runtime.stop()

            await asyncio.wait_for(stopped_future, timeout=5.0)

    def send_message(self, record: ExtensionRecord, message: ipc.Event, request_id: int | None = None) -> None:
        """
        Sends a JSON message to the extension if it is running.
        """
        if runtime := self.runtimes.get(record.id):
            runtime.send_message(message, request_id)

    def save_user_preferences(self, record: ExtensionRecord, data: Any) -> None:
        from ulauncher.api.event import EventType

        old_preferences = {p_id: pref.value for p_id, pref in record.preferences.items()}
        record.persist_preferences(data)
        for p_id, new_value in data.get("preferences", {}).items():
            # Only notify about values changing for preferences declared in the manifest
            if p_id in old_preferences and new_value != old_preferences[p_id]:
                event_data: ipc.UpdatePreferencesEvent = {
                    "type": EventType.UPDATE_PREFERENCES,
                    "args": (p_id, new_value, old_preferences[p_id]),
                }
                self.send_message(record, event_data)

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

        While the preview is active, the record with this id launches from the dev path; its
        dependencies are installed by the CLI before this is called.
        """

        logger.info("[preview] Previewing ext_id=%s path=%s debugger=%s", ext_id, path, with_debugger)
        self.preview = PreviewExtensionRecord(ext_id, path, with_debugger=with_debugger)

        # Guard the restart against a stop_preview that races in during the stop: only relaunch if
        # this preview is still the active one, otherwise stop_preview owns restoring the extension.
        def start_if_still_previewing() -> None:
            if self.preview and self.preview.id == ext_id:
                self._run_batch_job([ext_id], ["start"])

        # Relaunch from the dev path, stopping any conflicting installed instances
        self._run_batch_job([ext_id], ["stop"], callback=start_if_still_previewing)

    @events.on
    def stop_preview(self) -> None:
        """Stop the active preview and restore the installed extension. Triggered from the CLI via D-Bus"""
        if not self.preview:
            # will happen if preview is interrupted before started
            logger.debug("[preview] Ignoring stop_preview; no preview active")
            return

        ext_id = self.preview.id
        logger.info("[preview] Stopping preview %s", ext_id)

        def restore_original() -> None:
            self.preview = None
            # Reload from the installed path, or drop the record if the extension was never installed.
            record = self.get(ext_id)
            if record and record.is_enabled:
                self._run_batch_job([ext_id], ["start"])

        self._run_batch_job([ext_id], ["stop"], callback=restore_original)


ext_service = ExtensionService()
