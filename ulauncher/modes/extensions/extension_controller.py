from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime
from os.path import isfile, join
from pathlib import Path
from shutil import move, rmtree
from typing import Any, Callable

from ulauncher import cli, paths
from ulauncher.data import BaseDataClass, JsonConf
from ulauncher.gi import GLib
from ulauncher.internals import ipc
from ulauncher.modes.extensions import ext_exceptions, extension_finder
from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies
from ulauncher.modes.extensions.extension_manifest import (
    ExtensionManifest,
    ExtensionManifestPreference,
)
from ulauncher.modes.extensions.extension_remote import ExtensionRemote
from ulauncher.modes.extensions.extension_runtime import DEBUGPY_HOST, DEBUGPY_PORT, ExtensionRuntime
from ulauncher.modes.extensions.extension_supervisor import supervisor
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.json_utils import json_load


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

events = EventBus()


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


def _swap_dir(new_dir: str, target: str) -> bool:
    """Replace `target` with `new_dir`, rolling back to the original on failure. Returns whether it succeeded."""
    previous = f"{new_dir}.bak"
    # A stale .bak would be an existing dir, so move() nests target inside it instead of replacing.
    rmtree(previous, ignore_errors=True)
    backed_up = False
    if Path(target).exists():
        try:
            move(target, previous)
            backed_up = True
        except OSError:
            logger.exception("Could not back up the current version of %s; keeping it in place", target)
            rmtree(new_dir, ignore_errors=True)
            return False
    try:
        move(new_dir, target)
    except OSError:
        logger.exception("Could not swap extension into %s; keeping the previous version", target)
        # A cross-device move can fail after partially creating target; clear it before restoring.
        rmtree(target, ignore_errors=True)
        if backed_up:
            try:
                move(previous, target)
            except OSError:
                logger.exception("Could not restore the previous version of %s; it remains at %s", target, previous)
        rmtree(new_dir, ignore_errors=True)
        return False
    rmtree(previous, ignore_errors=True)
    return True


class ExtensionController:
    """Manages the lifecycle of an extension."""

    id: str
    path: str
    state: ExtensionState
    _state_path: Path

    def __init__(self, ext_id: str, path: str) -> None:
        self.id = ext_id
        self.path = path
        _state_path = f"{paths.EXTENSIONS_STATE}/{self.id}.json"
        self._state_path = Path(_state_path)
        self.state = ExtensionState.load(_state_path)
        self._seed_default_state()

    def _seed_default_state(self) -> None:
        """Seed a brand-new extension's state from its bundled .default-state.json. No-op once seeded,
        or while the files are absent, so an install that downloads them later seeds afterward."""
        if self.state.id or not Path(self.path).exists():
            return
        self.state.id = self.id
        self.state.update(json_load(f"{self.path}/.default-state.json"))

    @classmethod
    async def install(cls, url: str, commit_hash: str | None = None) -> ExtensionController:
        logger.info("Installing extension: %s", url)
        remote = ExtensionRemote(url)
        is_new_install = not Path(remote.target_dir).exists()  # noqa: ASYNC240
        if not is_new_install:
            logger.info('Extension with URL "%s" is already installed. Updating', remote.url)

        controller = cls(remote.ext_id, remote.target_dir)
        await controller._install(remote, commit_hash, url=url)
        logger.info("Extension %s installed successfully", controller.id)
        return controller

    @property
    def is_preview(self) -> bool:
        return supervisor.get_preview(self.id) is not None

    @property
    def source_path(self) -> str:
        """Where to load and launch the extension from: the dev path while it is being previewed,
        otherwise `self.path`."""
        return preview.path if (preview := supervisor.get_preview(self.id)) else self.path

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
    def owns_runtime(self) -> bool:
        """Whether the extension is running and owned by the current runtime (always False outside of the app)."""
        # supervisor.is_owner check for making the behavior/contract explicit, but not actually needed
        return supervisor.is_owner and self.id in supervisor.runtimes

    @property
    def is_manageable(self) -> bool:
        return extension_finder.is_manageable(self.path)

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
        from ulauncher.api.shared.event import EventType

        old_preferences = {p_id: pref.value for p_id, pref in self.preferences.items()}
        user_prefs_json = _load_preferences(self.id)
        user_prefs_json.save(data)
        if not self.owns_runtime:
            return
        for p_id, new_value in data.get("preferences", {}).items():
            # Only notify about values changing for preferences declared in the manifest
            if p_id in old_preferences and new_value != old_preferences[p_id]:
                event_data: ipc.UpdatePreferencesEvent = {
                    "type": EventType.UPDATE_PREFERENCES,
                    "args": (p_id, new_value, old_preferences[p_id]),
                }
                self.send_message(event_data)

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

    async def _install(self, remote: ExtensionRemote, commit_hash: str | None, **extra_state: Any) -> None:
        """Install (atomically): download, stop, swap and restart (if previously running).

        `extra_state` is merged into the saved state (install records the source url; update adds nothing).
        """
        target_path = self.path
        # Fixed path per extension so failed installs don't accumulate.
        # Concurrent installs of the same id clobber each other (wouldn't have worked anyway).
        staging_dir = str(Path(paths.EXTENSIONS_STAGING) / self.id)
        rmtree(staging_dir, ignore_errors=True)
        Path(staging_dir).mkdir(parents=True)  # noqa: ASYNC240
        remote.target_dir = staging_dir
        should_restart = False
        try:
            downloaded_hash, commit_timestamp = _run_gio_blocking(
                lambda on_success, on_error: remote.download(on_success, on_error, commit_hash)
            )
            _run_gio_blocking(ExtensionDependencies(remote.ext_id, staging_dir).install)
            # preview extensions need not and should not be restarted (they run from the dev paths)
            should_restart = self.owns_runtime and not self.is_preview
            if should_restart:
                await self.stop()
            if not _swap_dir(staging_dir, target_path):
                msg = f"Failed to swap the staged extension into {target_path}"
                raise OSError(msg)
            ExtensionManifest.load(target_path, force=True)  # bust the path cache so the swapped-in files win
            self._seed_default_state()
            self.state.save(
                **extra_state,
                browser_url=remote.browser_url or "",
                commit_hash=downloaded_hash,
                commit_time=datetime.fromtimestamp(commit_timestamp).isoformat(),
                updated_at=datetime.now().isoformat(),
                error_type="",
                error_message="",
            )
        finally:
            rmtree(staging_dir, ignore_errors=True)
            if should_restart:
                self.start()

    async def update(self) -> bool:
        """
        :returns: False if already up-to-date, True if was updated
        """
        logger.debug("Checking for updates to %s", self.id)
        has_update, commit_hash = await self.check_update()
        if not has_update:
            logger.info('Extension "%s" is already on the latest version', self.id)
            return False

        logger.info(
            'Updating extension "%s" from commit %s to %s',
            self.id,
            self.state.commit_hash[:8],
            commit_hash[:8],
        )

        try:
            await self._install(ExtensionRemote(self.state.url), commit_hash)
        except (ext_exceptions.ExtensionError, OSError):
            logger.exception("Could not update extension '%s'", self.id)
            raise
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
        if not supervisor.is_owner:
            msg = "Only the app process can start extensions. Ask it to via a D-Bus event ('extensions:reload')."
            raise RuntimeError(msg)

        if self.owns_runtime:
            return True  # if already started, count as successful

        def exit_handler(cause: str, error_msg: str) -> None:
            listeners = supervisor.stopped_listeners.get(self.id, [])
            for stop_listener in listeners:
                stop_listener()

            listeners.clear()

            if cause != "Stopped":
                logger.error('Extension "%s" exited with an error: %s (%s)', self.id, error_msg, cause)
                supervisor.runtimes.pop(self.id, None)
                # A failing preview must not disable the installed extension by persisting its error.
                if not self.is_preview:
                    self.state.save(error_type=cause, error_message=error_msg)

                events.emit("extensions:errored", self.id)

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
        if (preview_ext := supervisor.get_preview(self.id)) and preview_ext.with_debugger:
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
            supervisor.runtimes[self.id] = ExtensionRuntime(self.id, cmd, env, exit_handler)
        except (OSError, GLib.Error) as err:
            exit_handler("FailedToStart", str(err))
            return False
        events.emit("extensions:started", self.id)
        return self.owns_runtime

    async def stop(self) -> None:
        """Stops the extension process if this process owns one. Intentionally a no-op elsewhere
        (the CLI): remote runtimes are stopped by sending D-Bus events to the app instead."""
        if runtime := supervisor.runtimes.pop(self.id, None):
            stopped_future: asyncio.Future[None] = asyncio.Future()
            supervisor.stopped_listeners[self.id].append(lambda: stopped_future.set_result(None))
            runtime.stop()

            await asyncio.wait_for(stopped_future, timeout=5.0)

    def send_message(self, message: ipc.Event, request_id: int | None = None) -> None:
        """
        Sends a JSON message to the extension if it is running.
        """
        if not supervisor.is_owner:
            msg = "Only the app process can message extensions."
            raise RuntimeError(msg)

        if runtime := supervisor.runtimes.get(self.id):
            runtime.send_message(message, request_id)


class PreviewExtensionController(ExtensionController):
    """An extension being previewed from a dev path via the CLI.

    Only one runs at a time (the debugger binds a fixed port). This controller launches from the dev
    `path` (with `with_debugger`) instead of the extension's installed location.
    """

    with_debugger = False

    def __init__(self, ext_id: str, path: str, with_debugger: bool = False) -> None:
        super().__init__(ext_id, path)
        self.with_debugger = with_debugger
