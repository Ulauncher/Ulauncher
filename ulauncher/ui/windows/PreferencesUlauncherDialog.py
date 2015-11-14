# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: Bind a new key
import logging
import json
from gi.repository import Gio, Gtk, WebKit2
from locale import gettext as _

from ulauncher.utils.AutostartPreference import AutostartPreference
from ulauncher.utils.Settings import Settings
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.config import get_data_file
from ulauncher.utils.Router import Router, get_url_params
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
        self.init_styles(get_data_file('ui', 'preferences.css'))
        self._init_webview()
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
        self.webview.load_uri("file://%s" % get_data_file('ui', 'preferences', 'index.html'))

        web_settings = self.webview.get_settings()
        web_settings.set_enable_developer_extras(True)
        web_settings.set_enable_xss_auditor(False)
        web_settings.set_enable_write_console_messages_to_stdout(True)

        self.webview.get_context().register_uri_scheme('prefs', self.on_scheme_callback)

        inspector = self.webview.get_inspector()
        inspector.connect("attach", lambda inspector, target_view: WebKit2.WebView())

    ######################################
    # Overrides
    ######################################

    def present(self, page):
        # TODO: change URL hash
        super(PreferencesUlauncherDialog, self).present()

    def show(self, page):
        # TODO: change URL hash
        super(PreferencesUlauncherDialog, self).show()

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
            logger.warning('API call failed. %s: %s' % (type(e).__name__, e.message))
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
            logger.warning('Unexpected API error. %s: %s' % (type(e).__name__, e.message))

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
            'autostart-enabled': self.autostart_pref.is_on()
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

    @rt.route('/set/hotkey-show-app')
    def prefs_set_hotkey_show_app(self, url_params):
        hotkey = url_params['query']['value']
        logger.info('Set hotkey-show-app to %s' % hotkey)

        # Bind a new key
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        UlauncherWindow.get_instance().bind_show_app_hotkey(hotkey)
        self.settings.set_property('hotkey-show-app', hotkey)
        self.settings.save_to_file()

    @rt.route('/show/hotkey-dialog')
    def prefs_showhotkey_dialog(self, url_params):
        self._hotkey_name = url_params['query']['name']
        logger.info('Show hotkey-dialog for %s' % self._hotkey_name)
        self.hotkey_dialog.present()

    ######################################
    # Helpers
    ######################################

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
