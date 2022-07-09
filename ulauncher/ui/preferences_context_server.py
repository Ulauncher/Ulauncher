import os
import logging
import json
import mimetypes
from urllib.parse import unquote, urlparse
from typing import List, Optional, cast
import traceback

import gi
gi.require_versions({"Gtk": "3.0", "WebKit2": "4.0"})
# pylint: disable=wrong-import-position,unused-argument
from gi.repository import Gio, Gtk, WebKit2

from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.ui.windows.HotkeyDialog import HotkeyDialog
from ulauncher.api.shared.event import PreferencesUpdateEvent
from ulauncher.modes.extensions.extension_finder import find_extensions
from ulauncher.modes.extensions.ExtensionPreferences import ExtensionPreferences, PreferenceItems
from ulauncher.modes.extensions.ExtensionDb import ExtensionDb
from ulauncher.modes.extensions.ExtensionRunner import ExtensionRunner, ExtRunError
from ulauncher.modes.extensions.ExtensionManifest import ExtensionManifestError
from ulauncher.modes.extensions.ExtensionDownloader import (ExtensionDownloader, ExtensionIsUpToDateError)
from ulauncher.api.shared.errors import UlauncherAPIError, ExtensionError
from ulauncher.modes.extensions.ExtensionServer import ExtensionServer
from ulauncher.utils.Theme import load_available_themes
from ulauncher.utils.decorator.glib_idle_add import glib_idle_add
from ulauncher.utils.decorator.singleton import singleton
from ulauncher.utils.mypy_extensions import TypedDict
from ulauncher.utils.decorator.run_async import run_async
from ulauncher.utils.environment import IS_X11
from ulauncher.utils.icon import get_icon_path
from ulauncher.utils.Settings import Settings
from ulauncher.utils.Router import Router
from ulauncher.utils.systemd_controller import UlauncherSystemdController
from ulauncher.modes.shortcuts.ShortcutsDb import ShortcutsDb
from ulauncher.config import API_VERSION, VERSION, EXTENSIONS_DIR

logger = logging.getLogger()
rt = Router()


class PrefsApiError(UlauncherAPIError):
    pass


ExtError = TypedDict('ExtError', {
    'errorName': str,
    'message': str
})

ExtensionInfo = TypedDict('ExtensionInfo', {
    'id': str,
    'url': str,
    'updated_at': str,
    'last_commit': str,
    'last_commit_time': str,
    'name': str,
    'icon': str,
    'description': str,
    'developer_name': str,
    'instructions': Optional[str],
    'is_running': bool,
    'runtime_error': Optional[ExtRunError],
    'preferences': PreferenceItems,
    'error': Optional[ExtError]
})


def get_extension_info(ext_id: str, prefs: ExtensionPreferences, error: ExtError = None) -> ExtensionInfo:
    controllers = ExtensionServer.get_instance().controllers
    ext_db = ExtensionDb.load()
    is_connected = ext_id in controllers
    ext_runner = ExtensionRunner.get_instance()
    is_running = is_connected or ext_runner.is_running(ext_id)
    ext_db_record = ext_db.get(ext_id)
    # Controller method `get_icon_path` would work, but only running extensions have controllers
    icon = get_icon_path(prefs.manifest.icon, base_path=f"{EXTENSIONS_DIR}/{ext_id}")

    return {
        'id': ext_id,
        'url': ext_db_record.url,
        'updated_at': ext_db_record.updated_at,
        'last_commit': ext_db_record.last_commit,
        'last_commit_time': ext_db_record.last_commit_time,
        'name': prefs.manifest.name,
        'icon': icon,
        'description': prefs.manifest.description,
        'developer_name': prefs.manifest.developer_name,
        'instructions': prefs.manifest.instructions,
        'preferences': prefs.get_items(),
        'error': error,
        'is_running': is_running,
        'runtime_error': ext_runner.get_extension_error(ext_id) if not is_running else None
    }


def get_all_extensions() -> List[ExtensionInfo]:
    extensions = []
    for ext_id, _ in find_extensions(EXTENSIONS_DIR):
        prefs = ExtensionPreferences.create_instance(ext_id)  # type: ExtensionPreferences
        error = None
        try:
            prefs.manifest.validate()
            prefs.manifest.check_compatibility()
        except UlauncherAPIError as e:
            error = cast(ExtError, {
                'message': str(e),
                'errorName': e.error_name
            })
        except Exception as e:
            error = cast(ExtError, {
                'message': str(e),
                'errorName': ExtensionError.Other.value
            })
        extensions.append(get_extension_info(ext_id, prefs, error))

    return extensions


# pylint: disable=too-many-public-methods
class PreferencesContextServer():
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
        self.context.register_uri_scheme('prefs', self.on_scheme_callback)
        self.context.register_uri_scheme('file2', self.serve_file)
        self.context.set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)  # disable caching

    @run_async
    def serve_file(self, scheme_request):
        """
        Serves file with custom file2:// protocol because file:// breaks for some
        """
        # pylint: disable=broad-except
        try:
            params = urlparse(scheme_request.get_uri())
            [mime_type, _] = mimetypes.guess_type(params.path)
            stream = Gio.file_new_for_path(params.path).read()
            scheme_request.finish(stream, -1, mime_type)
        except Exception as e:
            logger.exception('Unable to send file. %s: %s', type(e).__name__, e)
            return

    @run_async
    def on_scheme_callback(self, scheme_request):
        """
        Handles Javascript-to-Python calls
        """

        # pylint: disable=broad-except
        try:
            params = urlparse(scheme_request.get_uri())
            query = json.loads(unquote(params.query))
            callback_name = query['callback']
            assert callback_name
        except Exception as e:
            logger.exception('API call failed. %s: %s', type(e).__name__, e)
            return

        try:
            resp = rt.dispatch(self, scheme_request.get_uri())
            callback = f'{callback_name}({json.dumps(resp)});'
        except Exception as e:
            error_type = type(e).__name__
            error_name = ExtensionError.Other.value
            if isinstance(e, UlauncherAPIError):
                logger.error('%s: %s', error_type, e)
                error_name = e.error_name
            else:
                logger.exception('Unexpected API error. %s: %s', error_type, e)

            err_meta = json.dumps({
                'message': str(e),
                'type': error_type,
                'errorName': error_name,
                'stacktrace': traceback.format_exc()
            })
            callback = f'{callback_name}(null, {err_meta});'

        try:
            stream = Gio.MemoryInputStream.new_from_data(callback.encode())
            # send response
            scheme_request.finish(stream, -1, 'text/javascript')
        except Exception as e:
            logger.exception('Unexpected API error. %s: %s', type(e).__name__, e)

    def notify_client(self, name, data):
        self.client.run_javascript(f'onNotification("{name}", {json.dumps(data)})')

    ######################################
    # Route handlers
    ######################################

    @rt.route('/get/all')
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

    @rt.route('/set')
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

    @rt.route('/set/hotkey-show-app')
    @glib_idle_add
    def set_hotkey_show_app(self, query):
        hotkey = query['value']
        # Bind a new key
        self.application.bind_hotkey(hotkey)
        self.settings.save(hotkey_show_app=hotkey)

    @rt.route('/show/hotkey-dialog')
    @glib_idle_add
    def show_hotkey_dialog(self, _):
        logger.info("Show hotkey-dialog")
        hotkey_dialog = HotkeyDialog()
        hotkey_dialog.connect(
            "hotkey-set",
            lambda _, val, caption: self.notify_client("hotkey-show-app", {"value": val, "caption": caption})
        )
        hotkey_dialog.present()

    @rt.route('/show/file-chooser')
    @glib_idle_add
    def show_file_chooser(self, query):
        """
        Request params: type=(image|all), name=(str)
        """
        file_browser_name = query['name']
        logger.info('Show file browser dialog for %s', file_browser_name)
        dialog = Gtk.FileChooserDialog("Please choose a file", self, Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Image files")
        filter_images.add_mime_type("image/*")
        dialog.add_filter(filter_images)

        response = dialog.run()
        data = {
            'value': None
        }
        if response == Gtk.ResponseType.OK:
            data['value'] = dialog.get_filename()

        logger.debug('%s %s', file_browser_name, data)
        self.notify_client(file_browser_name, data)
        dialog.destroy()

    @rt.route('/open/web-url')
    def open_url(self, query):
        url = query['url']
        logger.info('Open Web URL %s', url)
        OpenAction(url).run()

    @rt.route('/open/extensions-dir')
    def open_extensions_dir(self, _):
        logger.info('Open extensions directory "%s" in default file manager.', EXTENSIONS_DIR)
        OpenAction(EXTENSIONS_DIR).run()

    @rt.route('/shortcut/get-all')
    def shortcut_get_all(self, query):
        logger.info('Handling /shortcut/get-all')
        return list(ShortcutsDb.load().values())

    @rt.route('/shortcut/update')
    @rt.route('/shortcut/add')
    def shortcut_update(self, query):
        logger.info('Add/Update shortcut: %s', json.dumps(query))
        shortcuts = ShortcutsDb.load()
        id = shortcuts.add(query)
        shortcuts.save()
        return {'id': id}

    @rt.route('/shortcut/remove')
    def shortcut_remove(self, query):
        logger.info('Remove shortcut: %s', json.dumps(query))
        shortcuts = ShortcutsDb.load()
        del shortcuts[query['id']]
        shortcuts.save()

    @rt.route('/extension/get-all')
    def extension_get_all(self, query):
        logger.info('Handling /extension/get-all')
        return get_all_extensions()

    @rt.route('/extension/add')
    def extension_add(self, query):
        url = query['url']
        logger.info('Add extension: %s', url)
        downloader = ExtensionDownloader.get_instance()
        ext_id = downloader.download(url)
        ExtensionRunner.get_instance().run(ext_id)

        return get_all_extensions()

    @rt.route('/extension/update-prefs')
    def extension_update_prefs(self, query):
        logger.info('Update extension preferences: %s', query)
        controller = ExtensionServer.get_instance().controllers.get(query['id'])
        for pref_id, value in query['data'].items():
            old_value = controller.preferences.get(pref_id)['value']
            controller.preferences.set(pref_id, value)
            if value != old_value:
                controller.trigger_event(PreferencesUpdateEvent(pref_id, old_value, value))

    @rt.route('/extension/check-updates')
    def extension_check_updates(self, query):
        logger.info('Handling /extension/check-updates')
        try:
            return ExtensionDownloader.get_instance().get_new_version(query['id'])
        except ExtensionIsUpToDateError:
            return None

    @rt.route('/extension/update-ext')
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

    @rt.route('/extension/remove')
    def extension_remove(self, query):
        ext_id = query['id']
        logger.info('Remove extension: %s', ext_id)
        ExtensionRunner.get_instance().stop(ext_id)
        ExtensionDownloader.get_instance().remove(ext_id)
