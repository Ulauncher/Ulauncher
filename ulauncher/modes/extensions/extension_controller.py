from __future__ import annotations

import asyncio
import json
import logging
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from os.path import isfile, join
from pathlib import Path
from shutil import copytree, rmtree
from typing import Any, Callable

from ulauncher import cli, paths
from ulauncher.data import BaseDataClass, JsonConf
from ulauncher.gi import GLib
from ulauncher.modes.extensions import ext_exceptions, extension_finder
from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies
from ulauncher.modes.extensions.extension_manifest import (
    ExtensionManifest,
    ExtensionManifestPreference,
)
from ulauncher.modes.extensions.extension_remote import ExtensionRemote
from ulauncher.modes.extensions.extension_runtime import ExtensionRuntime
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.json_utils import json_load

DEBUGPY_HOST = "127.0.0.1"
DEBUGPY_PORT = 5678


class ExtensionPreference(ExtensionManifestPreference):
    value: str | int | bool | None = None


class ExtensionControllerTrigger(BaseDataClass):
    name = ""
    description = ""
    default_keyword = ""
    icon = ""
    keyword = ""


class ExtensionState(JsonConf):
    id = ""
    url = ""
    browser_url = ""
    updated_at = ""
    commit_hash = ""
    commit_time = ""
    is_enabled = True
    error_message = ""
    error_type = ""

    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        if key == "last_commit":
            key = "commit_hash"
        elif key == "last_commit_time":
            key = "commit_time"
        super().__setitem__(key, value)


logger = logging.getLogger(__name__)
extension_runtimes: dict[str, ExtensionRuntime] = {}
stopped_listeners: dict[str, list[Callable[[], None]]] = defaultdict(list)

events = EventBus()


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


preview = PreviewExtension()


def _run_gio_blocking(start: Callable[[Callable[[Any], None], Callable[[Exception], None]], None]) -> Any:
    """Drive a callback-based Gio operation to completion synchronously on the calling thread.

    Temporary bridge for step one of the asyncio/threading removal: extension_remote is now
    callback-based, but ExtensionController is still async and runs in worker threads (ext_handlers)
    or the CLI's asyncio loop. Gio.Subprocess callbacks dispatch on a GLib main context, not the
    asyncio loop, and no GLib loop runs in those threads, so a plain asyncio.Future shim would
    never resolve. Running a private GLib main loop (pushed as the thread-default context) drives
    the operation to completion. Remove this when the controller becomes callback-native.
    """
    context = GLib.MainContext.new()
    context.push_thread_default()
    box: dict[str, Any] = {}
    completed = False
    try:
        loop = GLib.MainLoop.new(context, False)

        def finish(result: Any = None, error: Exception | None = None) -> None:
            nonlocal completed
            box["result"], box["error"] = result, error
            completed = True
            loop.quit()

        start(finish, lambda error: finish(error=error))
        # done() can fire synchronously during start() (e.g. an immediate validation failure
        # that calls back without spawning a subprocess). Then loop.quit() already ran before
        # loop.run(), which GLib does not treat as a pending quit, so running the loop would
        # block forever. Only enter the loop while the callback is still pending.
        if not completed:
            loop.run()
    finally:
        # Always restore the thread-default context, even if start() raises synchronously
        # (a synchronous raise propagates to the caller, matching the pre-conversion behavior).
        context.pop_thread_default()
    if box.get("error"):
        raise box["error"]
    return box.get("result")


def _load_preferences(ext_id: str) -> JsonConf:
    return JsonConf.load(f"{paths.EXTENSIONS_CONFIG}/{ext_id}.json")


class ExtensionController:
    """Manages the lifecycle of an extension."""

    id: str
    path: str
    state: ExtensionState
    is_manageable: bool
    _state_path: Path

    def __init__(self, ext_id: str, path: str) -> None:
        self.id = ext_id
        self.path = path
        self.is_manageable = extension_finder.is_manageable(path)
        _state_path = f"{paths.EXTENSIONS_STATE}/{self.id}.json"
        self._state_path = Path(_state_path)
        self.state = ExtensionState.load(_state_path)

        if not self.state.id:
            self.state.id = self.id
            defaults = json_load(f"{path}/.default-state.json")
            self.state.update(defaults)

    @classmethod
    async def install(
        cls, url: str, commit_hash: str | None = None, warn_if_overwrite: bool = True
    ) -> ExtensionController:
        logger.info("Installing extension: %s", url)
        remote = ExtensionRemote(url)
        is_new_install = not Path(remote.target_dir).exists()  # noqa: ASYNC240
        downloaded_hash, commit_timestamp = _run_gio_blocking(
            lambda on_success, on_error: remote.download(on_success, on_error, commit_hash, warn_if_overwrite)
        )

        try:
            # install python dependencies from requirements.txt
            deps = ExtensionDependencies(remote.ext_id, remote.target_dir)
            _run_gio_blocking(deps.install)
        except ext_exceptions.DependencyError:
            # clean up broken install
            rmtree(remote.target_dir)
            raise

        controller = cls(remote.ext_id, remote.target_dir)
        controller.state.save(
            url=url,
            browser_url=remote.browser_url or "",
            commit_hash=downloaded_hash,
            commit_time=datetime.fromtimestamp(commit_timestamp).isoformat(),
            updated_at=datetime.now().isoformat(),
            error_type="",
            error_message="",
        )
        logger.info("Extension %s installed successfully", controller.id)
        if is_new_install:
            events.emit("extension_lifecycle:installed", controller)
        return controller

    @property
    def is_preview(self) -> bool:
        return preview.ext_id == self.id

    @property
    def source_path(self) -> str:
        """Where to load and launch the extension from: the dev path while it is being previewed,
        otherwise `self.path`."""
        return preview.path if self.is_preview else self.path

    @property
    def manifest(self) -> ExtensionManifest:
        return ExtensionManifest.load(self.source_path)

    @property
    def is_enabled(self) -> bool:
        return self.is_preview or (self.state.is_enabled and not self.has_error)

    @property
    def has_error(self) -> bool:
        # A preview must not surface the installed extension's persisted error; it reports as a preview.
        return not self.is_preview and bool(self.state.error_type)

    @property
    def is_running(self) -> bool:
        return self.id in extension_runtimes

    @property
    def preferences(self) -> dict[str, ExtensionPreference]:
        prefs_json = _load_preferences(self.id)
        prefs = {}
        for p_id, manifest_pref in self.manifest.preferences.items():
            # copy to avoid mutating
            pref = ExtensionPreference(**manifest_pref)
            pref.value = prefs_json.get("preferences", {}).get(p_id, manifest_pref.default_value)
            prefs[p_id] = pref
        return prefs

    @property
    def triggers(self) -> dict[str, ExtensionControllerTrigger]:
        user_prefs_json = _load_preferences(self.id)
        triggers = {}
        for t_id, manifest_trigger in self.manifest.triggers.items():
            trigger = ExtensionControllerTrigger(manifest_trigger)
            trigger.keyword = user_prefs_json.get("triggers", {}).get(t_id, {}).get("keyword", trigger.default_keyword)
            triggers[t_id] = trigger

        return triggers

    def save_user_preferences(self, data: Any) -> None:
        old_preferences = {p_id: pref.value for p_id, pref in self.preferences.items()}
        user_prefs_json = _load_preferences(self.id)
        user_prefs_json.save(data)
        events.emit("extensions:update_preferences", self.id, {**data, "old_preferences": old_preferences})

    def get_icon_value(self, icon: str | None = None) -> str:
        icon_value = icon or self.manifest.icon
        expanded_path = join(self.source_path, icon_value)
        if isfile(expanded_path):
            return expanded_path
        return icon_value

    async def remove(self) -> None:
        if not self.is_manageable:
            logger.warning(
                "Extension %s is not manageable. Cannot remove it automatically. "
                "Please remove it manually from the extensions directory: %s",
                self.id,
                self.path,
            )
            return

        await self.stop()
        rmtree(self.path)
        logger.info("Extension %s uninstalled successfully", self.id)

        if self._state_path.is_file():
            self._state_path.unlink()

        events.emit("extension_lifecycle:removed", self.id)

    async def update(self) -> bool:
        """
        :returns: False if already up-to-date, True if was updated
        """
        logger.debug("Checking for updates to %s", self.id)
        has_update, commit_hash = await self.check_update()
        was_running = self.is_running

        if not has_update:
            logger.info('Extension "%s" is already on the latest version', self.id)
            return False

        logger.info(
            'Updating extension "%s" from commit %s to %s',
            self.id,
            self.state.commit_hash[:8],
            commit_hash[:8],
        )

        # Backup extension files. If update fails, restore from backup
        with tempfile.TemporaryDirectory(prefix="ulauncher_ext_") as backup_dir:
            # use local variable, because self.path property will call locate() on a non-existing path
            ext_path = self.path
            copytree(ext_path, backup_dir, dirs_exist_ok=True)

            try:
                await self.stop()
                await self.install(self.state.url, commit_hash, warn_if_overwrite=False)
            except (ext_exceptions.ExtensionError, ValueError):
                logger.exception("Could not update extension '%s'.", self.id)
                copytree(backup_dir, ext_path, dirs_exist_ok=True)
                if was_running:
                    self.start()
                raise

        if was_running:
            self.start()
        logger.info("Successfully updated extension: %s", self.id)

        return True

    async def check_update(self) -> tuple[bool, str]:
        """
        Returns tuple with commit info about a new version
        """
        commit_hash = _run_gio_blocking(ExtensionRemote(self.state.url).get_compatible_hash)
        has_update = self.state.commit_hash != commit_hash
        return has_update, commit_hash

    async def toggle_enabled(self, enabled: bool) -> bool:
        self.state.save(is_enabled=enabled, error_type="", error_message="")
        if enabled:
            return self.start()
        await self.stop()
        return False

    def start(self) -> bool:
        """
        Starts the extension in a subprocess
        Returns True if the extension was already running or successfully started, False otherwise.
        """
        if self.is_running:
            return True  # if already started, count as successful

        def exit_handler(cause: str, error_msg: str) -> None:
            listeners = stopped_listeners.get(self.id, [])
            for stop_listener in listeners:
                stop_listener()

            listeners.clear()

            if cause != "Stopped":
                logger.error('Extension "%s" exited with an error: %s (%s)', self.id, error_msg, cause)
                extension_runtimes.pop(self.id, None)
                # A failing preview must not disable the installed extension by persisting its error.
                if not self.is_preview:
                    self.state.save(error_type=cause, error_message=error_msg)

            events.emit("extensions:exited", self.id, cause)

        try:
            self.manifest.validate()
            self.manifest.check_compatibility(verbose=True)
        except ext_exceptions.ManifestError as err:
            exit_handler("Invalid", str(err))
            return False
        except ext_exceptions.CompatibilityError as err:
            exit_handler("Incompatible", str(err))
            return False

        if not self.is_preview:
            self.state.save(error_type="", error_message="")  # clear any previous error

        ext_deps = ExtensionDependencies(self.id, self.source_path)
        extension_main = f"{self.source_path}/main.py"
        cmd = [sys.executable, extension_main]

        # Preview extensions can opt into the remote debugger
        if self.is_preview and preview.with_debugger:
            cmd = [
                sys.executable,
                "-m",
                "debugpy",
                "--listen",
                f"{DEBUGPY_HOST}:{DEBUGPY_PORT}",
                "--wait-for-client",
                extension_main,
            ]

        prefs = {p_id: pref.value for p_id, pref in self.preferences.items()}
        triggers = {t_id: t.default_keyword for t_id, t in self.manifest.triggers.items() if t.default_keyword}
        # backwards compatible v2 preferences format (with keywords added back)
        v2_prefs = {**triggers, **prefs}
        env = {
            "VERBOSE": str(int(cli.get_args().verbose)),
            "PYTHONPATH": ":".join(x for x in [paths.APPLICATION, ext_deps.get_dependencies_path()] if x),
            "EXTENSION_PREFERENCES": json.dumps(v2_prefs, separators=(",", ":")),
            "ULAUNCHER_EXTENSION_ID": self.id,
            "ULAUNCHER_INPUT_DEBOUNCE": str(self.manifest.input_debounce),
        }

        # socketpair/spawnv can fail for host-environment reasons (fd exhaustion, fork limits,
        # missing interpreter). Route these through exit_handler like a crash so the error is
        # surfaced consistently and any queued start listeners get cleaned up, rather than
        # raising out into callers.
        try:
            extension_runtimes[self.id] = ExtensionRuntime(self.id, cmd, env, exit_handler)
        except (OSError, GLib.Error) as err:
            exit_handler("FailedToStart", str(err))
            return False
        return self.is_running

    async def stop(self) -> None:
        if runtime := extension_runtimes.pop(self.id, None):
            stopped_future: asyncio.Future[None] = asyncio.Future()
            stopped_listeners[self.id].append(lambda: stopped_future.set_result(None))
            runtime.stop()

            await asyncio.wait_for(stopped_future, timeout=5.0)

    def send_message(self, message: dict[str, Any]) -> None:
        """
        Sends a JSON message to the extension if it is running.
        """
        if runtime := extension_runtimes.get(self.id):
            runtime.send_message(message)
