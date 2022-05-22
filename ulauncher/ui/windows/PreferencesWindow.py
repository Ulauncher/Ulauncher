# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: Bind a new key
import os
import logging
import json
import mimetypes
from urllib.parse import unquote, urlparse
from typing import List, Optional, cast
import traceback

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

# pylint: disable=wrong-import-position,unused-argument
from gi.repository import Gio, Gdk, Gtk, WebKit2, GLib

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
from ulauncher.utils.Theme import themes, load_available_themes
from ulauncher.utils.decorator.glib_idle_add import glib_idle_add
from ulauncher.utils.mypy_extensions import TypedDict
from ulauncher.utils.decorator.run_async import run_async
from ulauncher.utils.environment import IS_X11
from ulauncher.utils.Settings import Settings
from ulauncher.utils.Router import Router
from ulauncher.utils.AutostartPreference import AutostartPreference
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.modes.shortcuts.ShortcutsDb import ShortcutsDb
from ulauncher.config import get_asset, get_options, API_VERSION, VERSION, EXTENSIONS_DIR

logger = logging.getLogger(__name__)
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


# pylint: disable=too-many-public-methods, attribute-defined-outside-init
class PreferencesWindow(Gtk.ApplicationWindow):
    def __init__(self):
        super().__init__(
            title="Ulauncher Preferences",
            window_position=Gtk.WindowPosition.CENTER,
        )
        self.connect("key-press-event", self.on_key_press)
        self.connect("delete-event", self.on_delete)
        self.set_default_size(1000, 600)
        self.settings = Settings.get_instance()
        self._init_webview()
        self.autostart_pref = AutostartPreference()
        self.hotkey_dialog = HotkeyDialog()
        self.hotkey_dialog.connect('hotkey-set', self.on_hotkey_set)
        self.show_all()

    def on_key_press(self, _, event):
        keyval = event.get_keyval()
        keyname = Gdk.keyval_name(keyval[1])

        if keyname == 'Escape':
            self.hide()

    def on_delete(self, *_):
        # Override default event when the user presses the close button in the menubar
        self.hide()
        return True

    def _init_webview(self):
        """
        Initialize preferences WebView
        """
        settings = WebKit2.Settings(
            enable_developer_extras=bool(get_options().dev),
            enable_write_console_messages_to_stdout=True,
            enable_xss_auditor=False,
            hardware_acceleration_policy=WebKit2.HardwareAccelerationPolicy.NEVER,
        )

        context = WebKit2.WebContext()
        context.register_uri_scheme('prefs', self.on_scheme_callback)
        context.register_uri_scheme('file2', self.serve_file)
        context.set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)  # disable caching

        self.webview = WebKit2.WebView(settings=settings, web_context=context)
        self.add(self.webview)
        self._load_prefs_html()
        self.webview.connect('context-menu', self.webview_on_context_menu)

        inspector = self.webview.get_inspector()
        inspector.connect("attach", lambda inspector, target_view: WebKit2.WebView())

    ######################################
    # Overrides
    ######################################

    # pylint: disable=arguments-differ
    def present(self, page):
        self._load_prefs_html(page)
        super().present()

    def show(self, page):
        self._load_prefs_html(page)
        super().show()

    ######################################
    # GTK event handlers
    ######################################

    def webview_on_context_menu(self, *args):
        return bool(not get_options().dev)

    ######################################
    # WebView communication methods
    ######################################

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

    def send_webview_notification(self, name, data):
        self.webview.run_javascript(f'onNotification("{name}", {json.dumps(data)})')

    ######################################
    # Request handlers
    ######################################

    @rt.route('/get/all')
    def prefs_get_all(self, query):
        logger.info('API call /get/all')
        settings = self.settings.get_all()
        settings.update({
            'autostart_allowed': self.autostart_pref.is_allowed(),
            'autostart_enabled': self.autostart_pref.is_enabled(),
            'available_themes': self._get_available_themes(),
            'hotkey_show_app': self.get_app_hotkey(),
            'env': {
                'version': VERSION,
                'api_version': API_VERSION,
                'user_home': os.path.expanduser('~'),
                'is_x11': IS_X11,
            }
        })
        return settings

    @rt.route('/set')
    def prefs_set(self, query):
        property = query['property']
        value = query['value']
        # This setting is not stored to the config
        if property == 'autostart-enabled':
            self.prefs_set_autostart(value)
            return

        self.settings.set_property(property, value)

        if property == 'show-indicator-icon':
            # pylint: disable=import-outside-toplevel
            from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
            ulauncher_window = UlauncherWindow.get_instance()
            GLib.idle_add(AppIndicator.get_instance(ulauncher_window).switch, value)
        if property == 'theme-name':
            self.prefs_apply_theme()

    def prefs_set_autostart(self, is_enabled):
        logger.info('Set autostart-enabled to %s', is_enabled)
        if is_enabled and not self.autostart_pref.is_allowed():
            raise PrefsApiError("Unable to turn on autostart preference")

        try:
            self.autostart_pref.switch(is_enabled)
        except Exception as err:
            raise PrefsApiError(f'Caught an error while switching "autostart": {err}') from err

    def prefs_apply_theme(self):
        # pylint: disable=import-outside-toplevel
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        ulauncher_window = UlauncherWindow.get_instance()
        ulauncher_window.init_theme()

    @rt.route('/set/hotkey-show-app')
    @glib_idle_add
    def prefs_set_hotkey_show_app(self, query):
        hotkey = query['value']
        # Bind a new key
        # pylint: disable=import-outside-toplevel
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        ulauncher_window = UlauncherWindow.get_instance()
        ulauncher_window.bind_hotkey(hotkey)
        self.settings.set_property('hotkey-show-app', hotkey)

    @rt.route('/show/hotkey-dialog')
    @glib_idle_add
    def prefs_showhotkey_dialog(self, query):
        self._hotkey_name = query['name']
        logger.info('Show hotkey-dialog for %s', self._hotkey_name)
        self.hotkey_dialog.present()

    @rt.route('/show/file-browser')
    @glib_idle_add
    def prefs_show_file_browser(self, query):
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
        self.send_webview_notification(file_browser_name, data)
        dialog.destroy()

    @rt.route('/open/web-url')
    def prefs_open_url(self, query):
        url = query['url']
        logger.info('Open Web URL %s', url)
        OpenAction(url).run()

    @rt.route('/open/extensions-dir')
    def prefs_open_extensions_dir(self, _):
        logger.info('Open extensions directory "%s" in default file manager.', EXTENSIONS_DIR)
        OpenAction(EXTENSIONS_DIR).run()

    @rt.route('/shortcut/get-all')
    def prefs_shortcut_get_all(self, query):
        logger.info('Handling /shortcut/get-all')
        shortcuts = ShortcutsDb.get_instance()
        return shortcuts.get_shortcuts()

    @rt.route('/shortcut/update')
    @rt.route('/shortcut/add')
    def prefs_shortcut_update(self, query):
        logger.info('Add/Update shortcut: %s', json.dumps(query))
        shortcuts = ShortcutsDb.get_instance()
        id = shortcuts.put_shortcut(query['name'],
                                    query['keyword'],
                                    query['cmd'],
                                    query.get('icon') or None,
                                    str_to_bool(query['is_default_search']),
                                    str_to_bool(query['run_without_argument']),
                                    query.get('id'))
        shortcuts.commit()
        return {'id': id}

    @rt.route('/shortcut/remove')
    def prefs_shortcut_remove(self, query):
        logger.info('Remove shortcut: %s', json.dumps(query))
        shortcuts = ShortcutsDb.get_instance()
        shortcuts.remove(query['id'])
        shortcuts.commit()

    @rt.route('/extension/get-all')
    def prefs_extension_get_all(self, query):
        logger.info('Handling /extension/get-all')
        return self._get_all_extensions()

    @rt.route('/extension/add')
    def prefs_extension_add(self, query):
        url = query['url']
        logger.info('Add extension: %s', url)
        downloader = ExtensionDownloader.get_instance()
        ext_id = downloader.download(url)
        ExtensionRunner.get_instance().run(ext_id)

        return self._get_all_extensions()

    @rt.route('/extension/update-prefs')
    def prefs_extension_update_prefs(self, query):
        logger.info('Update extension preferences: %s', query)
        controller = ExtensionServer.get_instance().controllers.get(query['id'])
        for pref_id, value in query['data'].items():
            old_value = controller.preferences.get(pref_id)['value']
            controller.preferences.set(pref_id, value)
            if value != old_value:
                controller.trigger_event(PreferencesUpdateEvent(pref_id, old_value, value))

    @rt.route('/extension/check-updates')
    def prefs_extension_check_updates(self, query):
        logger.info('Handling /extension/check-updates')
        try:
            return ExtensionDownloader.get_instance().get_new_version(query['id'])
        except ExtensionIsUpToDateError:
            return None

    @rt.route('/extension/update-ext')
    def prefs_extension_update_ext(self, query):
        logger.info('Update extension: %s', query['id'])
        downloader = ExtensionDownloader.get_instance()
        try:
            downloader.update(query['id'])
        except ExtensionManifestError as e:
            raise PrefsApiError(e) from e

    @rt.route('/extension/remove')
    def prefs_extension_remove(self, query):
        logger.info('Remove extension: %s', query['id'])
        downloader = ExtensionDownloader.get_instance()
        downloader.remove(query['id'])

    ######################################
    # Helpers
    ######################################

    def _get_all_extensions(self) -> List[ExtensionInfo]:
        extensions = []
        for ext_id, _ in find_extensions(EXTENSIONS_DIR):
            prefs = ExtensionPreferences.create_instance(ext_id)  # type: ExtensionPreferences
            prefs.manifest.refresh()
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
            extensions.append(self._get_extension_info(ext_id, prefs, error))

        return extensions

    def _get_extension_info(self, ext_id: str, prefs: ExtensionPreferences, error: ExtError = None) -> ExtensionInfo:
        ext_db = ExtensionDb.get_instance()
        is_connected = ext_id in ExtensionServer.get_instance().controllers
        ext_runner = ExtensionRunner.get_instance()
        is_running = is_connected or ext_runner.is_running(ext_id)
        ext_db_record = ext_db.find(ext_id, {})
        return {
            'id': ext_id,
            'url': ext_db_record.get('url'),
            'updated_at': ext_db_record.get('updated_at'),
            'last_commit': ext_db_record.get('last_commit'),
            'last_commit_time': ext_db_record.get('last_commit_time'),
            'name': prefs.manifest.get_name(),
            'icon': prefs.manifest.get_icon_path(),
            'description': prefs.manifest.get_description(),
            'developer_name': prefs.manifest.get_developer_name(),
            'instructions': prefs.manifest.get_instructions(),
            'preferences': prefs.get_items(),
            'error': error,
            'is_running': is_running,
            'runtime_error': ext_runner.get_extension_error(ext_id) if not is_running else None
        }

    def _load_prefs_html(self, page=''):
        self.webview.load_uri(f"file2://{get_asset('preferences', 'index.html')}#/{page}")

    def _get_available_themes(self):
        load_available_themes()
        return [dict(value=th.get_name(), text=th.get_display_name()) for th in themes.values()]

    def get_app_hotkey(self):
        app_hotkey_current_accel_name = self.settings.get_property('hotkey-show-app')
        try:
            (key, mode) = Gtk.accelerator_parse(app_hotkey_current_accel_name)
        # pylint: disable=broad-except
        except Exception:
            logger.warning('Unable to parse accelerator "%s". Use Ctrl+Space', app_hotkey_current_accel_name)
            (key, mode) = Gtk.accelerator_parse("<Primary>space")
        return Gtk.accelerator_get_label(key, mode)

    def on_hotkey_set(self, widget, hotkey_val, hotkey_display_val):
        self.send_webview_notification(self._hotkey_name, {
            'value': hotkey_val,
            'displayValue': hotkey_display_val
        })


def str_to_bool(value):
    return value in [1, 'true', 'True']
