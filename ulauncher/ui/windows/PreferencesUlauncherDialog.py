# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: Bind a new key
import logging
import json
from gi.repository import Gio, Gtk, Gdk, GLib, Keybinder, WebKit2
from locale import gettext as _

from ulauncher.utils.AutostartPreference import AutostartPreference
from ulauncher.utils.Settings import Settings
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.config import get_data_file
from ulauncher.utils.Router import Router, get_url_params
from .PreferencesDialogBase import PreferencesDialogBase


logger = logging.getLogger(__name__)
rt = Router()

FORBIDDEN_ACCEL_KEYS = ('Delete', 'Page_Down', 'Page_Up', 'Home', 'End', 'Up', 'Down', 'Left', 'Right', 'Return',
                        'BackSpace', 'Alt_L', 'Alt_R', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'space',
                        'Escape', 'Tab', 'Insert')


class PrefsApiError(RuntimeError):
    pass


class PreferencesUlauncherDialog(PreferencesDialogBase):
    __gtype_name__ = "PreferencesUlauncherDialog"

    _hotkey_name = None

    ######################################
    # Initialization
    ######################################

    def finish_initializing(self, builder):
        """Set up the preferences dialog"""
        super(PreferencesUlauncherDialog, self).finish_initializing(builder)

        # unnecessary action area can be removed only manually, like this
        self.builder.get_object('dialog_action_area').destroy()

        self.settings = Settings.get_instance()
        self._init_styles()
        self._init_webview()
        self._init_hotkey_dialog()
        self._autostart_pref = AutostartPreference()

        self.show_all()

    def _init_webview(self):
        """
        Initialize preferences WebView
        """
        self.webview = WebKit2.WebView()
        self.builder.get_object('scrolled_window').add(self.webview)
        self.webview.load_uri("file://%s" % get_data_file('ui', 'preferences', 'index.html'))

        web_settings = self.webview.get_settings()
        web_settings.set_enable_developer_extras(True)
        web_settings.set_enable_xss_auditor(False)
        web_settings.set_enable_write_console_messages_to_stdout(True)

        self.webview.get_context().register_uri_scheme('prefs', self.on_scheme_callback)

        inspector = self.webview.get_inspector()
        inspector.connect("attach", lambda inspector, target_view: WebKit2.WebView())

    def _init_hotkey_dialog(self):
        self.hotkey_dialog = self.builder.get_object('hotkey-dialog')
        self.hotkey_input = self.builder.get_object('hotkey-input')

        def on_delete(*args):
            # don't delete. Hide instead
            self.hotkey_dialog.hide()
            return True

        self.builder.get_object('hotkey_dialog_action_area').destroy()
        self.hotkey_dialog.connect('delete-event', on_delete)

        self.hotkey_input.set_text('')
        self.hotkey_input.connect('key-press-event', self.on_hotkey_press_event)

    def _init_styles(self):
        self.provider = Gtk.CssProvider()
        self.provider.load_from_path(get_data_file('ui', 'preferences.css'))
        self._apply_css(self, self.provider)
        self.screen = self.get_screen()
        self.visual = self.screen.get_rgba_visual()
        if self.visual is not None and self.screen.is_composited():
            self.set_visual(self.visual)

    def _apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        if isinstance(widget, Gtk.Container):
            widget.forall(self._apply_css, provider)

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
            callback = '%s(null, %s);' % (callback_name, e)
        except Exception as e:
            message = 'Unexpected API error. %s: %s' % (type(e).__name__, e.message)
            callback = '%s(null, %s);' % (callback_name, message)
            logger.warning(message)

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
            'autostart-allowed': self._autostart_pref.is_allowed(),
            'autostart-enabled': self._autostart_pref.is_on()
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
        if is_on and not self._autostart_pref.is_allowed():
            raise PrefsApiError("Unable to turn on autostart preference")

        try:
            self._autostart_pref.switch(is_on)
        except Exception as e:
            raise PrefsApiError('Caught an error while switching "autostart": %s' % e)

    @rt.route('/set/hotkey-show-app')
    def prefs_set_hotkey_show_app(self, url_params):
        hotkey = url_params['query']['value']
        logger.info('Set hotkey-show-app to %s' % hotkey)

        # Bind a new key
        # from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        # UlauncherWindow.get_instance().bind_show_app_hotkey(hotkey)

        # self.settings.set_property('hotkey-show-app', hotkey)
        # self.settings.save_to_file()

    @rt.route('/show/hotkey-dialog')
    def prefs_show_hotkey_dialog(self, url_params):
        self._hotkey_name = url_params['query']['name']
        logger.info('Show hotkey-dialog for %s' % self._hotkey_name)
        self.hotkey_dialog.present()

    ######################################
    # Helpers
    ######################################

    def _get_bool(self, str_val):
        return str(str_val).lower() in ('true', '1', 'on')

    def is_valid_hotkey(self, label, accel_name):
        """
        :param str label: String like 'Ctrl+`'
        :param str accel_name: String like '<Primary>space'

        accel_name should not be in FORBIDDEN_ACCEL_KEYS
        and label should consist of more than one symbol

        NOTE: it's very likely these verifications are not enough,
        but I could not find more information about this topic
        """

        return (accel_name not in FORBIDDEN_ACCEL_KEYS) and len(label) > 1 and not accel_name.startswith('KP_')

    def on_hotkey_press_event(self, widget, event):
        # remove GDK_MOD2_MASK, because it seems unnecessary
        mask = event.state
        if mask & Gdk.ModifierType.MOD2_MASK:
            mask ^= Gdk.ModifierType.MOD2_MASK

        display_name = Gtk.accelerator_get_label(event.keyval, mask)
        accel_name = Gtk.accelerator_name(event.keyval, mask)

        # do nothing for invalid hotkeys
        if not self.is_valid_hotkey(display_name, accel_name):
            logger.debug("Invalid hotkey '%s', ('%s') is not allowed" % (display_name, accel_name))
            return

        self.send_webview_notification('hotkey-set', {
            'name': self._hotkey_name,
            'value': accel_name,
            'displayValue': display_name
        })
        self.hotkey_input.set_text(display_name)
        self.hotkey_dialog.hide()

    def get_app_hotkey(self):
        app_hotkey_current_accel_name = self.settings.get_property('hotkey-show-app')
        try:
            (key, mode) = Gtk.accelerator_parse(app_hotkey_current_accel_name)
        except Exception:
            logger.warning('Unable to parse accelerator "%s". Use Ctrl+Space' % app_hotkey_current_accel_name)
            (key, mode) = Gtk.accelerator_parse("<Primary>space")
        return Gtk.accelerator_get_label(key, mode)
