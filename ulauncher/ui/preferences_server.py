from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import os
import traceback
from typing import Any, Callable, Coroutine
from urllib.parse import unquote, urlparse

from gi.repository import Gio, GLib, Gtk

from ulauncher import api_version, paths, version
from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.modes.shortcuts.shortcuts_db import ShortcutsDb
from ulauncher.utils.decorator.run_async import run_async
from ulauncher.utils.environment import IS_X11
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.hotkey_controller import HotkeyController
from ulauncher.utils.launch_detached import open_detached
from ulauncher.utils.settings import Settings
from ulauncher.utils.systemd_controller import SystemdController
from ulauncher.utils.theme import get_themes
from ulauncher.utils.webkit2 import WebKit2

logger = logging.getLogger()
events = EventBus()
routes: dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {}


# Python generics doesn't support this case, so we have to declare with ... and Any
def route(
    path: str,
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Callable[..., Coroutine[Any, Any, Any]]]:
    def decorator(handler: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
        routes[path] = handler
        return handler

    return decorator


def get_extension_data(controller: ExtensionController) -> dict[str, Any]:
    return {
        **controller.state,
        "path": controller.path,
        "duplicate_paths": [entry for entry in extension_finder.locate_iter(controller.id) if entry != controller.path],
        "name": controller.manifest.name,
        "icon": controller.get_normalized_icon_path(),
        "authors": controller.manifest.authors,
        "instructions": controller.manifest.instructions,
        "preferences": controller.user_preferences,
        "triggers": controller.user_triggers,
        "is_manageable": controller.is_manageable,
        "is_stopped": not controller.is_running,
    }


class PreferencesServer:
    """
    Handles the "back-end" of the PreferencesWindow's wekit webview
    Because of how the WebKitGtk API is implemented you should never create more than one context for the same mainloop
    register_uri_scheme must be called only once per scheme and context and this means whatever method you bind those to
    have to persist as long as the app is running.
    For this reason it should be separate from the window class, which is an object that you want to be able to create,
    destroy and recreate.
    """

    client: WebKit2.WebView

    def __init__(self) -> None:
        self.autostart_pref = SystemdController("ulauncher")
        self.settings = Settings.load()
        self.context = WebKit2.WebContext()
        self.context.register_uri_scheme("prefs", self.request_listener)
        self.context.set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)  # disable caching

    @run_async
    def request_listener(self, scheme_request: Any) -> None:
        """
        Handle requests using custom prefs:// protocol
        To avoid CORS issues both files and api requests has to go through here and you have to use
        the same domain (or skip the domain like now) for all urls, making all urls start with prefs:///
        (In addition some users has had issues with webkit directly loading files from file:///)
        """
        uri: str = scheme_request.get_uri()
        params = urlparse(uri)
        path = params.path.replace("null/", "/")

        if route_handler := routes.get(path):
            # WebKit.URISchemeRequest is very primitive as a server:
            # * It can only read the URL (not the body of a post request)
            # * It can either send data with status 200 or an error message which cannot be retrieved in the client.
            # So we have to invent our own ways to handle errors and passing data:
            # 1. Data is sent to the server as URL encoded JSON in the URL query string.
            # (because actual URL params is an old, terrible and lossy standard).
            # 2. The response is sent as an array "[data, error]".
            # In the future "finish_with_response" (new in version 2.36) could be used
            try:
                args = json.loads(unquote(params.query)) if params.query else []
                data = json.dumps([asyncio.run(route_handler(self, *args))])
            except Exception as e:
                err_type = type(e).__name__
                error = {"message": str(e), "type": err_type}
                logger.exception("Preferences server error: %s", err_type)

                if not err_type.endswith("RecoverableError"):
                    stack_details = {"stack trace": f"```\n{traceback.format_exc()}\n```"}
                    error["details"] = "\n".join([f"{k}: {v}" for k, v in {**error, **stack_details}.items()])

                data = json.dumps([None, error])

            error_stream = Gio.MemoryInputStream.new_from_data(data.encode())
            scheme_request.finish(error_stream, -1, "application/json")
            return

        if os.path.isfile(path):
            try:
                [mime_type, _] = mimetypes.guess_type(path)
                file_stream = Gio.file_new_for_path(path).read()
                scheme_request.finish(file_stream, -1, mime_type)
            except Exception as e:  # noqa: BLE001
                logger.warning("Couldn't handle file request from '%s' (%s: %s)", uri, type(e).__name__, e)
            else:
                return

        logger.warning("Unhandled request from '%s'.", uri)

    def notify_client(self, name: str, data: Any) -> None:
        self.client.run_javascript(f'onNotification("{name}", {json.dumps(data)})')

    ######################################
    # Route handlers
    ######################################

    @route("/get/all")
    async def get_all(self) -> dict[str, Any]:
        logger.info("API call /get/all")
        export_settings = self.settings.copy()
        export_settings["available_themes"] = [{"value": name, "text": name} for name in get_themes()]
        export_settings["autostart_enabled"] = self.autostart_pref.is_enabled()
        export_settings["env"] = {
            "autostart_allowed": self.autostart_pref.can_start(),
            "api_version": api_version,
            "hotkey_supported": HotkeyController.is_supported(),
            "version": version,
            "is_x11": IS_X11,
        }

        return export_settings

    @route("/set")
    async def apply_settings(self, prop: str, value: Any) -> None:
        logger.info("Setting %s to %s", prop, value)
        # This setting is no longer handled by / persisted to the config as of Ulauncher v6
        if prop == "autostart_enabled":
            self.apply_autostart(value)
            return

        if prop == "daemonless":
            events.emit("app:toggle_hold", not value)
            if value is True:
                self.autostart_pref.stop()

        self.settings.save({prop: value})

        if prop == "show_tray_icon":
            events.emit("app:toggle_tray_icon", value)

    def apply_autostart(self, is_enabled: bool) -> None:
        logger.info("Set autostart_enabled to %s", is_enabled)
        if is_enabled and not self.autostart_pref.can_start():
            msg = "Unable to turn on autostart preference"
            raise RuntimeError(msg)

        try:
            self.autostart_pref.toggle(is_enabled)
        except Exception as err:
            msg = f'Caught an error while switching "autostart": {err}'
            raise RuntimeError(msg) from err

    @route("/show/hotkey-dialog")
    async def show_hotkey_dialog(self) -> None:
        logger.info("Show hotkey-dialog")
        HotkeyController.show_dialog()

    @route("/show/file-chooser")
    async def show_file_chooser(self, name: str, mime_filter: dict[str, str]) -> None:
        logger.info("Show file browser dialog for %s", name)
        GLib.idle_add(self._show_file_chooser, name, mime_filter)

    def _show_file_chooser(self, name: str, mime_filter: dict[str, str]) -> None:
        fc_dialog = Gtk.FileChooserDialog(title="Please choose a file")
        fc_dialog.add_button("_Open", Gtk.ResponseType.OK)
        fc_dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        fc_dialog.set_default_response(Gtk.ResponseType.OK)

        if mime_filter and isinstance(mime_filter, dict):
            file_filter = Gtk.FileFilter()
            for filter_name, filter_mime in mime_filter.items():
                file_filter.set_name(filter_name)
                file_filter.add_mime_type(filter_mime)
            fc_dialog.add_filter(file_filter)
        response = fc_dialog.run()
        if response == Gtk.ResponseType.OK:
            value = fc_dialog.get_filename()
            self.notify_client(name, {"value": value})
        fc_dialog.close()

    @route("/open/web-url")
    async def open_url(self, url: str) -> None:
        logger.info("Open Web URL %s", url)
        open_detached(url)

    @route("/open/extensions-dir")
    async def open_extensions_dir(self) -> None:
        logger.info('Open extensions directory "%s" in default file manager.', paths.USER_EXTENSIONS)
        open_detached(paths.USER_EXTENSIONS)

    @route("/shortcut/get-all")
    async def shortcut_get_all(self) -> list[dict[str, Any]]:
        logger.info("Handling /shortcut/get-all")
        shortcuts = []
        for shortcut in ShortcutsDb.load().values():
            if shortcut.icon:
                shortcut.icon = os.path.expanduser(shortcut.icon)
            shortcuts.append(shortcut)
        return shortcuts

    @route("/shortcut/update")
    async def shortcut_update(self, shortcut: dict[str, Any]) -> None:
        logger.info("Add/Update shortcut: %s", json.dumps(shortcut))
        shortcuts = ShortcutsDb.load()
        shortcuts.save({shortcut["id"]: shortcut})

    @route("/shortcut/remove")
    async def shortcut_remove(self, shortcut_id: str) -> None:
        logger.info("Remove shortcut: %s", json.dumps(shortcut_id))
        shortcuts = ShortcutsDb.load()
        shortcuts.save({shortcut_id: None})

    @route("/extension/get-all")
    async def extension_get_all(self, reload: bool) -> dict[str, dict[str, Any]]:
        logger.info("Handling /extension/get-all")
        if reload:
            tasks = [controller.start() for controller in ExtensionController.iterate() if controller.is_enabled]
            await asyncio.gather(*tasks)
        return {ex.id: get_extension_data(ex) for ex in ExtensionController.iterate()}

    @route("/extension/add")
    async def extension_add(self, url: str) -> dict[str, Any]:
        logger.info("Add extension: %s", url)
        controller = ExtensionController.create_from_url(url)
        await controller.install()
        await controller.stop()
        await controller.start()
        return get_extension_data(controller)

    @route("/extension/set-prefs")
    async def extension_update_prefs(self, ext_id: str, data: dict[str, Any]) -> None:
        logger.info("Update extension preferences %s to %s", ext_id, data)
        events.emit("extension:update_preferences", ext_id, data)
        # Note: Must save after emitting because the event above need access to
        # both the new and old data
        ExtensionController.create(ext_id).save_user_preferences(data)

    @route("/extension/check-update")
    async def extension_check_update(self, ext_id: str) -> tuple[bool, str]:
        logger.info("Checking if extension has an update")
        controller = ExtensionController.create(ext_id)
        return await controller.check_update()

    @route("/extension/update-ext")
    async def extension_update_ext(self, ext_id: str) -> dict[str, Any]:
        logger.info("Update extension: %s", ext_id)
        controller = ExtensionController.create(ext_id)
        await controller.update()
        return get_extension_data(controller)

    @route("/extension/remove")
    async def extension_remove(self, ext_id: str) -> None:
        logger.info("Remove extension: %s", ext_id)
        controller = ExtensionController.create(ext_id)
        await controller.remove()

    @route("/extension/toggle-enabled")
    async def extension_toggle_enabled(self, ext_id: str, is_enabled: bool) -> None:
        logger.info("Toggle extension: %s on: %s", ext_id, is_enabled)
        controller = ExtensionController.create(ext_id)
        await controller.toggle_enabled(is_enabled)
