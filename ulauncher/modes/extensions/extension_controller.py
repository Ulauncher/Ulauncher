from __future__ import annotations

import asyncio
import json
import logging
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from shutil import copytree, rmtree
from typing import Any, Callable

from ulauncher import paths
from ulauncher.cli import get_cli_args
from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.extension_dependencies import (
    ExtensionDependencies,
    ExtensionDependenciesRecoverableError,
)
from ulauncher.modes.extensions.extension_manifest import (
    ExtensionIncompatibleRecoverableError,
    ExtensionManifest,
    ExtensionManifestError,
    ExtensionManifestPreference,
    ExtensionManifestTrigger,
)
from ulauncher.modes.extensions.extension_remote import ExtensionRemote
from ulauncher.modes.extensions.extension_runtime import ExtensionRuntime
from ulauncher.utils.decorator.debounce import debounce
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.get_icon_path import get_icon_path
from ulauncher.utils.json_conf import JsonConf
from ulauncher.utils.json_utils import json_load


class ExtensionPreference(ExtensionManifestPreference):
    value: str | int | None = None


class ExtensionControllerTrigger(ExtensionManifestTrigger):
    pass


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


logger = logging.getLogger()
extension_runtimes: dict[str, ExtensionRuntime] = {}
stopped_listeners: dict[str, list[Callable[[], None]]] = defaultdict(list)

events = EventBus()


def _load_preferences(ext_id: str) -> JsonConf:
    return JsonConf.load(f"{paths.EXTENSIONS_CONFIG}/{ext_id}.json")


class ExtensionController:
    """Manages the lifecycle of an extension."""

    id: str
    path: str
    state: ExtensionState
    manifest: ExtensionManifest
    is_manageable: bool
    is_preview: bool = False
    shadowed_by_preview: bool = False
    debounced_send_message: Callable[[dict[str, Any]], None]
    _state_path: Path

    def __init__(self, ext_id: str, path: str) -> None:
        self.id = ext_id
        self.path = path
        self.manifest = ExtensionManifest.load(path)
        self.is_manageable = extension_finder.is_manageable(path)
        self.debounced_send_message = debounce(self.manifest.input_debounce)(self.send_message)
        self._state_path = Path(f"{paths.EXTENSIONS_STATE}/{self.id}.json")
        self.state = ExtensionState.load(self._state_path)

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
        is_new_install = not Path(remote.target_dir).exists()
        commit_hash, commit_timestamp = remote.download(commit_hash, warn_if_overwrite)

        try:
            # install python dependencies from requirements.txt
            deps = ExtensionDependencies(remote.ext_id, remote.target_dir)
            deps.install()
        except ExtensionDependenciesRecoverableError:
            # clean up broken install
            rmtree(remote.target_dir)
            raise

        controller = cls(remote.ext_id, remote.target_dir)
        controller.state.save(
            url=url,
            browser_url=remote.browser_url or "",
            commit_hash=commit_hash,
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
    def is_enabled(self) -> bool:
        return self.state.is_enabled and not self.has_error

    @property
    def has_error(self) -> bool:
        return bool(self.state.error_type)

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
            if user_keyword := user_prefs_json.get("triggers", {}).get(t_id, {}).get("keyword", trigger.keyword):
                trigger.keyword = user_keyword
            triggers[t_id] = trigger

        return triggers

    def save_user_preferences(self, data: Any) -> None:
        user_prefs_json = _load_preferences(self.id)
        user_prefs_json.save(data)

    def get_normalized_icon_path(self, icon: str | None = None) -> str | None:
        return get_icon_path(icon or self.manifest.icon, base_path=self.path)

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
            except Exception:
                logger.exception("Could not update extension '%s'.", self.id)
                copytree(backup_dir, ext_path, dirs_exist_ok=True)
                await self.toggle_enabled(was_running)
                raise

        await self.toggle_enabled(was_running)
        logger.info("Successfully updated extension: %s", self.id)

        return True

    async def check_update(self) -> tuple[bool, str]:
        """
        Returns tuple with commit info about a new version
        """
        commit_hash = ExtensionRemote(self.state.url).get_compatible_hash()
        has_update = self.state.commit_hash != commit_hash
        return has_update, commit_hash

    async def toggle_enabled(self, enabled: bool) -> bool:
        self.state.save(is_enabled=enabled, error_type="", error_message="")
        if enabled:
            return self.start()
        await self.stop()
        return False

    def start(self, with_debugger: bool = False) -> bool:
        if self.shadowed_by_preview:
            return False

        if not self.is_running:

            def exit_handler(cause: str, error_msg: str) -> None:
                listeners = stopped_listeners.get(self.id, [])
                for stop_listener in listeners:
                    stop_listener()

                listeners.clear()

                if cause != "Stopped":
                    logger.error('Extension "%s" exited with an error: %s (%s)', self.id, error_msg, cause)
                    extension_runtimes.pop(self.id, None)
                    self.state.save(error_type=cause, error_message=error_msg)

            try:
                self.manifest.validate()
                self.manifest.check_compatibility(verbose=True)
            except ExtensionManifestError as err:
                exit_handler("Invalid", str(err))
                return False
            except ExtensionIncompatibleRecoverableError as err:
                exit_handler("Incompatible", str(err))
                return False

            self.state.save(error_type="", error_message="")  # clear any previous error

            ext_deps = ExtensionDependencies(self.id, self.path)
            extension_main = f"{self.path}/main.py"
            cmd = [sys.executable, extension_main]

            # If debugger mode is enabled, prepend debugger command
            if with_debugger:
                cmd = [sys.executable, "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", extension_main]

            prefs = {p_id: pref.value for p_id, pref in self.preferences.items()}
            triggers = {t_id: t.keyword for t_id, t in self.manifest.triggers.items() if t.keyword}
            # backwards compatible v2 preferences format (with keywords added back)
            v2_prefs = {**triggers, **prefs}
            env = {
                "VERBOSE": str(int(get_cli_args().verbose)),
                "PYTHONPATH": ":".join(x for x in [paths.APPLICATION, ext_deps.get_dependencies_path()] if x),
                "EXTENSION_PREFERENCES": json.dumps(v2_prefs, separators=(",", ":")),
                "ULAUNCHER_EXTENSION_ID": self.id,
            }

            extension_runtimes[self.id] = ExtensionRuntime(self.id, cmd, env, exit_handler)
        return self.is_running

    async def stop(self) -> None:
        if runtime := extension_runtimes.pop(self.id, None):
            stopped_future: asyncio.Future[None] = asyncio.Future()
            stopped_listeners[self.id].append(lambda: stopped_future.set_result(None))
            runtime.stop()

            await asyncio.wait_for(stopped_future, timeout=5.0)

    def send_message(self, message: dict[str, Any]) -> bool:
        """
        Sends a JSON message to the extension if it is running.
        Returns True if message was sent, False otherwise.
        """
        if runtime := extension_runtimes.get(self.id):
            runtime.send_message(message)
            return True
        return False
