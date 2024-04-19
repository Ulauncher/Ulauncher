from __future__ import annotations

import json
import logging
import mimetypes
import os
import time
import traceback
from typing import Any, Callable, Generator, TypeVar
from urllib.parse import unquote, urlparse

from gi.repository import Gio, GLib, Gtk

from ulauncher.config import API_VERSION, PATHS, VERSION
from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.ExtensionController import ExtensionController
from ulauncher.modes.extensions.ExtensionSocketServer import ExtensionSocketServer
from ulauncher.modes.shortcuts.ShortcutsDb import ShortcutsDb
from ulauncher.utils.decorator.run_async import run_async
from ulauncher.utils.environment import IS_X11
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.hotkey_controller import HotkeyController
from ulauncher.utils.launch_detached import open_detached
from ulauncher.utils.Settings import Settings
from ulauncher.utils.systemd_controller import SystemdController
from ulauncher.utils.Theme import get_themes
from ulauncher.utils.WebKit2 import WebKit2

P1 = TypeVar("P1")
P2 = TypeVar("P2")
logger = logging.getLogger()
events = EventBus()
routes: dict[str, Callable[..., Any]] = {}


# Python generics doesn't support this case, so we have to declare with ... and Any
def route(path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
        routes[path] = handler
        return handler

    return decorator


def get_extensions() -> Generator[dict[str, Any], None, None]:
    for ext_id, ext_path in extension_finder.iterate():
        controller = ExtensionController.create(ext_id)

        yield {
            **controller.state,
            "path": ext_path,
            "duplicate_paths": [entry for entry in extension_finder.locate_iter(ext_id) if entry != ext_path],
            "name": controller.manifest.name,
            "icon": controller.get_normalized_icon_path(),
            "authors": controller.manifest.authors,
            "instructions": controller.manifest.instructions,
            "preferences": controller.user_preferences,
            "triggers": controller.user_triggers,
            "is_manageable": controller.is_manageable,
            "is_running": controller.is_running,
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
        route_handler = routes.get(path)

        if route_handler:
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
                data = json.dumps([route_handler(self, *args)])
            except Exception as e:
                err_type = type(e).__name__
                error = {"message": str(e), "type": err_type}
                logging.exception("Preferences server error: %s", err_type)

                if not err_type.endswith("Warning"):
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
            except Exception as e:
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
    def get_all(self) -> dict[str, Any]:
        logger.info("API call /get/all")
        export_settings = self.settings.copy()
        export_settings["available_themes"] = [{"value": name, "text": name} for name in get_themes()]
        export_settings["autostart_enabled"] = self.autostart_pref.is_enabled()
        export_settings["env"] = {
            "autostart_allowed": self.autostart_pref.can_start(),
            "api_version": API_VERSION,
            "hotkey_supported": HotkeyController.is_supported(),
            "version": VERSION,
            "is_x11": IS_X11,
        }

        return export_settings

    @route("/set")
    def apply_settings(self, prop: str, value: Any) -> None:
        logger.info("Setting %s to %s", prop, value)
        # This setting is not stored to the config
        if prop == "autostart_enabled":
            self.apply_autostart(value)
            return

        self.settings.update({prop: value})
        self.settings.save()

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
    def show_hotkey_dialog(self) -> None:
        logger.info("Show hotkey-dialog")
        HotkeyController.show_dialog()

    @route("/show/file-chooser")
    def show_file_chooser(self, name: str, mime_filter: dict[str, str]) -> None:
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
    def open_url(self, url: str) -> None:
        logger.info("Open Web URL %s", url)
        open_detached(url)

    @route("/open/extensions-dir")
    def open_extensions_dir(self) -> None:
        logger.info('Open extensions directory "%s" in default file manager.', PATHS.USER_EXTENSIONS)
        open_detached(PATHS.USER_EXTENSIONS)

    @route("/shortcut/get-all")
    def shortcut_get_all(self) -> list[dict[str, Any]]:
        logger.info("Handling /shortcut/get-all")
        shortcuts = []
        for shortcut in ShortcutsDb.load().values():
            if shortcut.icon:
                shortcut.icon = os.path.expanduser(shortcut.icon)
            shortcuts.append(shortcut)
        return shortcuts

    @route("/shortcut/update")
    def shortcut_update(self, shortcut: dict[str, Any]) -> None:
        logger.info("Add/Update shortcut: %s", json.dumps(shortcut))
        shortcuts = ShortcutsDb.load()
        shortcuts[shortcut["id"]] = shortcut
        shortcuts.save()

    @route("/shortcut/remove")
    def shortcut_remove(self, shortcut_id: str) -> None:
        logger.info("Remove shortcut: %s", json.dumps(shortcut_id))
        shortcuts = ShortcutsDb.load()
        del shortcuts[shortcut_id]
        shortcuts.save()

    @route("/extension/get-all")
    def extension_get_all(self, reload: bool) -> list[dict[str, Any]]:
        logger.info("Handling /extension/get-all")
        if reload:
            for controller in ExtensionController.iterate():
                if controller.is_enabled:
                    controller.start()
            # TODO(friday): Refactor so we can know when it has completed instead of hard coding
            time.sleep(0.5)
        return list(get_extensions())

    @route("/extension/add")
    def extension_add(self, url: str) -> list[dict[str, Any]]:
        logger.info("Add extension: %s", url)
        controller = ExtensionController.create_from_url(url)
        controller.download()
        controller.stop()
        controller.start()
        # TODO(friday): Refactor run so we can know when it has completed instead of hard coding
        time.sleep(0.5)
        return list(get_extensions())

    @route("/extension/set-prefs")
    def extension_update_prefs(self, ext_id: str, data: dict[str, Any]) -> None:
        logger.info("Update extension preferences %s to %s", ext_id, data)
        controller = ExtensionController.create(ext_id)
        socket_controller = ExtensionSocketServer().controllers.get(ext_id)
        if socket_controller:  # send update_preferences only if extension is running
            for id, new_value in data.get("preferences", {}).items():
                pref = controller.user_preferences.get(id)
                if pref and new_value != pref.value:
                    event_data = {"type": "event:update_preferences", "args": [id, new_value, pref.value]}
                    socket_controller.trigger_event(event_data)
        controller.save_user_preferences(data)

    @route("/extension/check-update")
    def extension_check_update(self, ext_id: str) -> tuple[bool, str]:
        logger.info("Checking if extension has an update")
        return ExtensionController.create(ext_id).check_update()

    @route("/extension/update-ext")
    def extension_update_ext(self, ext_id: str) -> None:
        logger.info("Update extension: %s", ext_id)
        ExtensionController.create(ext_id).update()

    @route("/extension/remove")
    def extension_remove(self, ext_id: str) -> None:
        logger.info("Remove extension: %s", ext_id)
        controller = ExtensionController.create(ext_id)
        controller.remove()

    @route("/extension/toggle-enabled")
    def extension_toggle_enabled(self, ext_id: str, is_enabled: bool) -> None:
        logger.info("Toggle extension: %s", ext_id)
        controller = ExtensionController.create(ext_id)
        controller.toggle_enabled(is_enabled)
