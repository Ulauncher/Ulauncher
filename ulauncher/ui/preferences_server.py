import os
import logging
import json
import mimetypes
from urllib.parse import unquote, urlparse
import traceback

import gi
gi.require_versions({"Gtk": "3.0", "WebKit2": "4.0"})
# pylint: disable=wrong-import-position,unused-argument
from gi.repository import Gio, Gtk, WebKit2

from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.ui.windows.HotkeyDialog import HotkeyDialog
from ulauncher.api.shared.event import PreferencesUpdateEvent
from ulauncher.modes.extensions.extension_finder import find_extensions
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifest, ExtensionManifestError
from ulauncher.modes.extensions.ExtensionDb import ExtensionDb
from ulauncher.modes.extensions.ExtensionRunner import ExtensionRunner
from ulauncher.modes.extensions.ExtensionDownloader import (ExtensionDownloader, ExtensionIsUpToDateError)
from ulauncher.api.shared.errors import UlauncherAPIError, ExtensionError
from ulauncher.modes.extensions.ExtensionServer import ExtensionServer
from ulauncher.utils.Theme import load_available_themes
from ulauncher.utils.decorator.glib_idle_add import glib_idle_add
from ulauncher.utils.decorator.singleton import singleton
from ulauncher.utils.decorator.run_async import run_async
from ulauncher.utils.environment import IS_X11
from ulauncher.utils.icon import get_icon_path
from ulauncher.utils.Settings import Settings
from ulauncher.utils.systemd_controller import UlauncherSystemdController
from ulauncher.modes.shortcuts.ShortcutsDb import ShortcutsDb
from ulauncher.config import API_VERSION, VERSION, EXTENSIONS_DIR

logger = logging.getLogger()
routes = {}


def route(path: str):
    def decorator(handler):
        routes[path] = handler
        return handler

    return decorator


class PrefsApiError(UlauncherAPIError):
    pass


def get_extension_info(ext_id: str, manifest: ExtensionManifest, error: str = None, error_name: str = None):
    controllers = ExtensionServer.get_instance().controllers
    ext_db = ExtensionDb.load()
    is_connected = ext_id in controllers
    ext_runner = ExtensionRunner.get_instance()
    is_running = is_connected or ext_runner.is_running(ext_id)
    ext_db_record = ext_db.get(ext_id)
    # Controller method `get_icon_path` would work, but only running extensions have controllers
    icon = get_icon_path(manifest.icon, base_path=f"{EXTENSIONS_DIR}/{ext_id}")

    return {
        'id': ext_id,
        'url': ext_db_record.url,
        'updated_at': ext_db_record.updated_at,
        'last_commit': ext_db_record.last_commit,
        'last_commit_time': ext_db_record.last_commit_time,
        'name': manifest.name,
        'icon': icon,
        'developer_name': manifest.developer_name,
        'instructions': manifest.instructions,
        'preferences': manifest.preferences,
        'error': {'message': error, 'errorName': error_name} if error else None,
        'is_running': is_running,
        'runtime_error': ext_runner.get_extension_error(ext_id) if not is_running else None
    }


def get_all_extensions():
    extensions = []
    for ext_id, _ in find_extensions(EXTENSIONS_DIR):
        manifest = ExtensionManifest.load_from_extension_id(ext_id)
        error = None
        error_name = None
        try:
            manifest.validate()
            manifest.check_compatibility()
        except UlauncherAPIError as e:
            error = str(e)
            error_name = e.error_name
        except Exception as e:
            error = str(e)
            error_name = ExtensionError.Other.value
        extensions.append(get_extension_info(ext_id, manifest, error, error_name))

    return extensions


# pylint: disable=too-many-public-methods
class PreferencesServer():
    """
    Handles the "back-end" of the PreferencesWindow's wekit webview
    Because of how the WebKitGtk API is implemented you should never create more than one context for the same mainloop
    register_uri_scheme must be called only once per scheme and context and this means whatever ethod you bind those to
    have to persist as long as the app is running.
    For this reason it should be separate from the window class, which is an object that you want to be able to create,
    destroy and recreate.
    """
    client: WebKit2.WebView

    @classmethod
    @singleton
    def get_instance(cls, application):
        return cls(application)

    def __init__(self, application):
        self.application = application
        self.autostart_pref = UlauncherSystemdController()
        self.settings = Settings.load()
        self.context = WebKit2.WebContext()
        self.context.register_uri_scheme('prefs', self.request_listener)
        self.context.set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)  # disable caching

    @run_async
    def request_listener(self, scheme_request):
        """
        Handle requests using custom prefs:// protocol
        To avoid CORS issues both files and api requests has to go through here and you have to use
        the same domain (or skip the domain like now) for all urls, making all urls start with prefs:///
        (In addition some users has had issues with webkit directly loading files from file:///)
        """
        uri = scheme_request.get_uri()
        params = urlparse(uri)
        route_handler = routes.get(params.path)

        if route_handler:
            # WebKit.URISchemeRequest is very primitive as a server:
            # * It can only read the URL (not the body of a post request)
            # * It can either send data with status 200 or an error with no data.
            # So we have to invent our own ways to handle errors and passing data:
            # 1. Data is sent to the server as URL encoded JSON in the URL query string.
            # (because actual URL params is an old, terrible and lossy standard).
            # 2. The response is sent as an array "[data, error]".
            # pylint: disable=broad-except
            try:
                query = json.loads(unquote(params.query)) if params.query else {}
                data = json.dumps([route_handler(self, query)])
            except Exception as e:
                error_type = type(e).__name__
                error_name = ExtensionError.Other.value
                if isinstance(e, UlauncherAPIError):
                    logger.error('%s: %s', error_type, e)
                    error_name = e.error_name
                else:
                    logger.exception('Unexpected API error. %s: %s', error_type, e)
                data = json.dumps([None, {
                    'message': str(e),
                    'type': error_type,
                    'errorName': error_name,
                    'stacktrace': traceback.format_exc()
                }])

            stream = Gio.MemoryInputStream.new_from_data(data.encode())
            scheme_request.finish(stream, -1, "application/json")
            return

        if os.path.isfile(params.path):
            # pylint: disable=broad-except
            try:
                [mime_type, _] = mimetypes.guess_type(params.path)
                stream = Gio.file_new_for_path(params.path).read()
                scheme_request.finish(stream, -1, mime_type)
                return
            except Exception as e:
                logger.warning("Couldn't handle file request from '%s' (%s: %s)", uri, type(e).__name__, e)

        logger.warning("Unhandled request from '%s'.", uri)

    def notify_client(self, name, data):
        self.client.run_javascript(f'onNotification("{name}", {json.dumps(data)})')

    ######################################
    # Route handlers
    ######################################

    @route('/get/all')
    def get_all(self, _):
        logger.info('API call /get/all')
        export_settings = self.settings.copy()
        themes = [dict(value=th.get_name(), text=th.get_display_name()) for th in load_available_themes().values()]

        hotkey_caption = "Ctrl+Space"
        try:
            hotkey_caption = Gtk.accelerator_get_label(*Gtk.accelerator_parse(self.settings.hotkey_show_app))
        # pylint: disable=broad-except
        except Exception:
            logger.warning('Unable to parse accelerator "%s". Use Ctrl+Space', self.settings.hotkey_show_app)

        export_settings.update({
            'autostart_allowed': self.autostart_pref.is_allowed(),
            'autostart_enabled': self.autostart_pref.is_enabled(),
            'available_themes': themes,
            'hotkey_show_app': hotkey_caption,
            'env': {
                'version': VERSION,
                'api_version': API_VERSION,
                'user_home': os.path.expanduser('~'),
                'is_x11': IS_X11,
            }
        })
        return export_settings

    @route('/set')
    def apply_settings(self, query):
        property = query['property']
        value = query['value']
        logger.info('Setting %s to %s', property, value)
        # This setting is not stored to the config
        if property == 'autostart-enabled':
            self.apply_autostart(value)
            return

        self.settings.save({property: value})

        if property == 'show_indicator_icon':
            self.application.toggle_appindicator(value)
        if property == 'theme_name':
            self.apply_theme()

    def apply_autostart(self, is_enabled):
        logger.info('Set autostart-enabled to %s', is_enabled)
        if is_enabled and not self.autostart_pref.is_allowed():
            raise PrefsApiError("Unable to turn on autostart preference")

        try:
            self.autostart_pref.switch(is_enabled)
        except Exception as err:
            raise PrefsApiError(f'Caught an error while switching "autostart": {err}') from err

    def apply_theme(self):
        self.application.window.init_theme()

    @route('/set/hotkey-show-app')
    @glib_idle_add
    def set_hotkey_show_app(self, query):
        hotkey = query['value']
        # Bind a new key
        self.application.bind_hotkey(hotkey)
        self.settings.save(hotkey_show_app=hotkey)

    @route('/show/hotkey-dialog')
    @glib_idle_add
    def show_hotkey_dialog(self, _):
        logger.info("Show hotkey-dialog")
        hotkey_dialog = HotkeyDialog()
        hotkey_dialog.connect(
            "hotkey-set",
            lambda _, val, caption: self.notify_client("hotkey-show-app", {"value": val, "caption": caption})
        )
        hotkey_dialog.present()

    @route('/show/file-chooser')
    @glib_idle_add
    def show_file_chooser(self, query):
        name, mime_filter = query
        logger.info('Show file browser dialog for %s', name)
        dialog = Gtk.FileChooserDialog(
            "Please choose a file",
            self.client.get_toplevel(),
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        if mime_filter and isinstance(mime_filter, dict):
            filter = Gtk.FileFilter()
            for filter_name, filter_mime in mime_filter.items():
                filter.set_name(filter_name)
                filter.add_mime_type(filter_mime)
            dialog.add_filter(filter)
        value = dialog.get_filename() if dialog.run() == Gtk.ResponseType.OK else None
        self.notify_client(name, {"value": value})

    @route('/open/web-url')
    def open_url(self, query):
        url = query['url']
        logger.info('Open Web URL %s', url)
        OpenAction(url).run()

    @route('/open/extensions-dir')
    def open_extensions_dir(self, _):
        logger.info('Open extensions directory "%s" in default file manager.', EXTENSIONS_DIR)
        OpenAction(EXTENSIONS_DIR).run()

    @route('/shortcut/get-all')
    def shortcut_get_all(self, query):
        logger.info('Handling /shortcut/get-all')
        return list(ShortcutsDb.load().values())

    @route('/shortcut/update')
    @route('/shortcut/add')
    def shortcut_update(self, query):
        logger.info('Add/Update shortcut: %s', json.dumps(query))
        shortcuts = ShortcutsDb.load()
        id = shortcuts.add(query)
        shortcuts.save()
        return {'id': id}

    @route('/shortcut/remove')
    def shortcut_remove(self, query):
        logger.info('Remove shortcut: %s', json.dumps(query))
        shortcuts = ShortcutsDb.load()
        del shortcuts[query['id']]
        shortcuts.save()

    @route('/extension/get-all')
    def extension_get_all(self, query):
        logger.info('Handling /extension/get-all')
        return get_all_extensions()

    @route('/extension/add')
    def extension_add(self, query):
        url = query['url']
        logger.info('Add extension: %s', url)
        downloader = ExtensionDownloader.get_instance()
        ext_id = downloader.download(url)
        ExtensionRunner.get_instance().run(ext_id)

        return get_all_extensions()

    @route('/extension/update-prefs')
    def extension_update_prefs(self, query):
        logger.info('Update extension preferences: %s', query)
        controller = ExtensionServer.get_instance().controllers.get(query['id'])
        for pref_id, value in query['data'].items():
            preference = controller.manifest.preferences.get(pref_id)
            old_value = preference.value
            preference.value = value
            controller.manifest.save_user_preferences(query['id'])
            if value != old_value:
                controller.trigger_event(PreferencesUpdateEvent(pref_id, old_value, value))

    @route('/extension/check-updates')
    def extension_check_updates(self, query):
        logger.info('Handling /extension/check-updates')
        try:
            return ExtensionDownloader.get_instance().get_new_version(query['id'])
        except ExtensionIsUpToDateError:
            return None

    @route('/extension/update-ext')
    def extension_update_ext(self, query):
        ext_id = query['id']
        logger.info('Update extension: %s', ext_id)
        try:
            runner = ExtensionRunner.get_instance()
            runner.stop(ext_id)
            ExtensionDownloader.get_instance().update(ext_id)
            runner.run(ext_id)
        except ExtensionManifestError as e:
            raise PrefsApiError(e) from e

    @route('/extension/remove')
    def extension_remove(self, query):
        ext_id = query['id']
        logger.info('Remove extension: %s', ext_id)
        ExtensionRunner.get_instance().stop(ext_id)
        ExtensionDownloader.get_instance().remove(ext_id)
