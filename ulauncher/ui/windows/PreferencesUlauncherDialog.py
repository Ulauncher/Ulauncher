# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: Bind a new key
import logging
import json

from gi.repository import Gio, Gtk, WebKit2
from locale import gettext as _
from urllib import unquote

from ulauncher.helpers import parse_options, force_unicode
from ulauncher.utils.AutostartPreference import AutostartPreference
from ulauncher.utils.Settings import Settings
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.result_list.item_action.OpenUrlAction import OpenUrlAction
from ulauncher.config import get_data_file, get_version
from ulauncher.utils.Router import Router, get_url_params
from ulauncher.search.shortcuts.ShortcutsDb import ShortcutsDb
from .Builder import Builder
from .WindowHelper import WindowHelper
from .HotkeyDialog import HotkeyDialog


logger = logging.getLogger(__name__)
rt = Router()


class PrefsApiError(RuntimeError):
    pass


class PreferencesUlauncherDialog(Gtk.Dialog, WindowHelper):
    __gtype_name__ = "PreferencesUlauncherDialog"

    _hotkey_name = None

    ######################################
    # Initialization
    ######################################

    def __new__(cls):
        """Special static method that's automatically called by Python when
        constructing a new instance of this class.

        Returns a fully instantiated PreferencesDialog object.
        """
        builder = Builder.new_from_file('PreferencesUlauncherDialog')
        new_object = builder.get_object("preferences_ulauncher_dialog")
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called while initializing this instance in __new__

        finish_initalizing should be called after parsing the ui definition
        and creating a PreferencesDialog object with it in order to
        finish initializing the start of the new PerferencesUlauncherDialog
        instance.

        Put your initialization code in here and leave __init__ undefined.
        """

        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self, True)

        # unnecessary action area can be removed only manually, like this
        self.ui['dialog_action_area'].destroy()

        self.settings = Settings.get_instance()
        self._init_webview()
        self.init_styles(get_data_file('styles', 'preferences.css'))
        self.autostart_pref = AutostartPreference()
        self.hotkey_dialog = HotkeyDialog()
        self.hotkey_dialog.connect('hotkey-set', self.on_hotkey_set)

        self.show_all()

    def _init_webview(self):
        """
        Initialize preferences WebView
        """
        self.webview = WebKit2.WebView()
        self.ui['scrolled_window'].add(self.webview)
        opts = parse_options()
        self._load_prefs_html()

        web_settings = self.webview.get_settings()
        web_settings.set_enable_developer_extras(bool(opts.dev))
        web_settings.set_enable_xss_auditor(False)
        web_settings.set_enable_write_console_messages_to_stdout(True)

        self.webview.get_context().register_uri_scheme('prefs', self.on_scheme_callback)
        self.webview.get_context().set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)  # disable caching
        self.webview.connect('button-press-event', self.webview_on_button_press_event)
        self.webview.connect('context-menu', self.webview_on_context_menu)

        inspector = self.webview.get_inspector()
        inspector.connect("attach", lambda inspector, target_view: WebKit2.WebView())

    ######################################
    # Overrides
    ######################################

    def present(self, page):
        self._load_prefs_html(page)
        super(PreferencesUlauncherDialog, self).present()

    def show(self, page):
        self._load_prefs_html(page)
        super(PreferencesUlauncherDialog, self).show()

    ######################################
    # GTK event handlers
    ######################################

    def webview_on_button_press_event(self, widget, event):
        """
        Makes preferences window draggable only by top block with a button bar
        400x60 - size of the button bar
        """
        window_width = self.get_size()[0]
        if event.button == 1 and 400 < event.x < window_width - 70 and 0 < event.y < 60:
            self.begin_move_drag(event.button, event.x_root, event.y_root, event.time)

        return False

    def webview_on_context_menu(self, *args):
        return bool(not parse_options().dev)

    ######################################
    # WebView communication methods
    ######################################

    def on_scheme_callback(self, schemeRequest):
        """
        Handles Javascript-to-Python calls
        """

        try:
            params = get_url_params(schemeRequest.get_uri())
            callback_name = params['query']['callback']
            assert callback_name
        except Exception as e:
            logger.exception('API call failed. %s: %s' % (type(e).__name__, e.message))
            return

        try:
            resp = rt.dispatch(self, schemeRequest.get_uri())
            callback = '%s(%s);' % (callback_name, json.dumps(resp))
        except PrefsApiError as e:
            callback = '%s(null, %s);' % (callback_name, json.dumps(e))
        except Exception as e:
            message = 'Unexpected API error. %s: %s' % (type(e).__name__, e.message)
            callback = '%s(null, %s);' % (callback_name, json.dumps(message))
            logger.exception(message)

        try:
            stream = Gio.MemoryInputStream.new_from_data(callback)
            # send response
            schemeRequest.finish(stream, -1, 'text/javascript')
        except Exception as e:
            logger.exception('Unexpected API error. %s: %s' % (type(e).__name__, e.message))

    def send_webview_notification(self, name, data):
        self.webview.run_javascript('onNotification("%s", %s)' % (name, json.dumps(data)))

    ######################################
    # Request handlers
    ######################################

    @rt.route('/get/all')
    def prefs_get_all(self, url_params):
        logger.info('API call /get/all')
        return {
            'show-indicator-icon': self.settings.get_property('show-indicator-icon'),
            'hotkey-show-app': self.get_app_hotkey(),
            'autostart-allowed': self.autostart_pref.is_allowed(),
            'autostart-enabled': self.autostart_pref.is_on(),
            'show-recent-apps': self.settings.get_property('show-recent-apps'),
            'theme-name': self.settings.get_property('theme-name'),
            'version': get_version()
        }

    @rt.route('/set/show-indicator-icon')
    def prefs_set_show_indicator_icon(self, url_params):
        show_indicator = self._get_bool(url_params['query']['value'])
        logger.info('Set show-indicator-icon to %s' % show_indicator)
        self.settings.set_property('show-indicator-icon', show_indicator)
        indicator = AppIndicator.get_instance()
        indicator.show() if show_indicator else indicator.hide()
        self.settings.save_to_file()

    @rt.route('/set/autostart-enabled')
    def prefs_set_autostart(self, url_params):
        is_on = self._get_bool(url_params['query']['value'])
        logger.info('Set autostart-enabled to %s' % is_on)
        if is_on and not self.autostart_pref.is_allowed():
            raise PrefsApiError("Unable to turn on autostart preference")

        try:
            self.autostart_pref.switch(is_on)
        except Exception as e:
            raise PrefsApiError('Caught an error while switching "autostart": %s' % e)

    @rt.route('/set/show-recent-apps')
    def prefs_set_show_recent_apps(self, url_params):
        is_on = self._get_bool(url_params['query']['value'])
        logger.info('Set show-recent-apps to %s' % is_on)
        self.settings.set_property('show-recent-apps', is_on)
        self.settings.save_to_file()

    @rt.route('/set/hotkey-show-app')
    def prefs_set_hotkey_show_app(self, url_params):
        hotkey = url_params['query']['value']
        logger.info('Set hotkey-show-app to %s' % hotkey)

        # Bind a new key
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        UlauncherWindow.get_instance().bind_show_app_hotkey(hotkey)
        self.settings.set_property('hotkey-show-app', hotkey)
        self.settings.save_to_file()

    @rt.route('/set/theme-name')
    def prefs_set_theme_name(self, url_params):
        name = url_params['query']['value']
        logger.info('Set theme-name to %s' % name)

        self.settings.set_property('theme-name', name)
        self.settings.save_to_file()

        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        UlauncherWindow.get_instance().init_theme()

    @rt.route('/show/hotkey-dialog')
    def prefs_showhotkey_dialog(self, url_params):
        self._hotkey_name = url_params['query']['name']
        logger.info('Show hotkey-dialog for %s' % self._hotkey_name)
        self.hotkey_dialog.present()

    @rt.route('/show/file-browser')
    def prefs_show_file_browser(self, url_params):
        """
        Request params: type=(image|all), name=(str)
        """
        file_browser_name = url_params['query']['name']
        logger.info('Show file browser dialog for %s' % file_browser_name)
        dialog = Gtk.FileChooserDialog("Please choose a file", self, Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Image files")
        filter_images.add_mime_type("image/*")
        dialog.add_filter(filter_images)

        response = dialog.run()
        data = {
            'name': file_browser_name,
            'path': None
        }
        if response == Gtk.ResponseType.OK:
            data['path'] = dialog.get_filename()

        logger.debug('file-select %s' % data)
        self.send_webview_notification('file-select', data)
        dialog.destroy()

    @rt.route('/open/web-url')
    def prefs_open_url(self, url_params):
        url = unquote(url_params['query']['url'])
        logger.info('Open Web URL %s' % url)
        OpenUrlAction(url).run()

    @rt.route('/close')
    def prefs_close(self, url_params):
        logger.info('Close preferences')
        self.hide()

    @rt.route('/shortcut/get-all')
    def prefs_shortcut_get_all(self, url_params):
        logger.info('Handling /shortcut/get-all')
        shortcuts = ShortcutsDb.get_instance()
        return shortcuts.get_sorted_records()

    @rt.route('/shortcut/update')
    @rt.route('/shortcut/add')
    def prefs_shortcut_update(self, url_params):
        req_data = url_params['query']
        logger.info('Add/Update shortcut: %s' % json.dumps(req_data))
        shortcuts = ShortcutsDb.get_instance()
        id = shortcuts.put_shortcut(force_unicode(req_data['name']),
                                    force_unicode(req_data['keyword']),
                                    force_unicode(req_data['cmd']),
                                    req_data['icon'],
                                    req_data['is_default_search'],
                                    req_data.get('id'))
        shortcuts.commit()
        return {'id': id}

    @rt.route('/shortcut/delete')
    def prefs_shortcut_delete(self, url_params):
        req_data = url_params['query']
        logger.info('Delete shortcut: %s' % json.dumps(req_data))
        shortcuts = ShortcutsDb.get_instance()
        id = shortcuts.remove(req_data['id'])
        shortcuts.commit()

    ######################################
    # Helpers
    ######################################

    def _load_prefs_html(self, page=''):
        self.webview.load_uri("file://%s#/%s" % (get_data_file('preferences', 'index.html'), page))

    def _get_bool(self, str_val):
        return str(str_val).lower() in ('true', '1', 'on')

    def get_app_hotkey(self):
        app_hotkey_current_accel_name = self.settings.get_property('hotkey-show-app')
        try:
            (key, mode) = Gtk.accelerator_parse(app_hotkey_current_accel_name)
        except Exception:
            logger.warning('Unable to parse accelerator "%s". Use Ctrl+Space' % app_hotkey_current_accel_name)
            (key, mode) = Gtk.accelerator_parse("<Primary>space")
        return Gtk.accelerator_get_label(key, mode)

    def on_hotkey_set(self, widget, hotkey_val, hotkey_display_val):
        self.send_webview_notification('hotkey-set', {
            'name': self._hotkey_name,
            'value': hotkey_val,
            'displayValue': hotkey_display_val
        })
