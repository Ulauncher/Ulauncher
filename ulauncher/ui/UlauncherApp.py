from __future__ import annotations

import logging
import time
from functools import lru_cache

from gi.repository import Gio, Gtk

from ulauncher.api.shared.query import Query
from ulauncher.config import APP_ID, FIRST_RUN
from ulauncher.modes.extensions.ExtensionRunner import ExtensionRunner
from ulauncher.modes.extensions.ExtensionServer import ExtensionServer
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.ui.windows.PreferencesWindow import PreferencesWindow
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
from ulauncher.utils.hotkey_controller import HotkeyController
from ulauncher.utils.Settings import Settings

logger = logging.getLogger()


class UlauncherApp(Gtk.Application, AppIndicator):
    """
    Main Ulauncher application (singleton)
    """

    # Gtk.Applications check if the app is already registered and if so,
    # new instances sends the signals to the registered one
    # So all methods except __init__ runs on the main app
    _query = ""
    window: UlauncherWindow | None = None
    preferences: PreferencesWindow | None = None

    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls):
        return cls()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs)
        self.connect("startup", self.setup)  # runs only once on the main instance

    @property
    def query(self) -> Query:
        return Query(self._query)

    @query.setter
    def query(self, value: str):
        self._query = value.lstrip()
        if self.window:
            self.window.input.set_text(self._query)
            self.window.input.set_position(-1)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        Gio.ActionMap.add_action_entries(
            self, [("show-preferences", self.show_preferences, None), ("set-query", self.activate_query, "s")]
        )

    def do_activate(self, *_args, **_kwargs):
        self.show_launcher()

    def do_command_line(self, *args, **_kwargs):
        # We need to use "--no-window" from the unique CLI invocation here,
        # Can't use config.get_options(), because that's the daemon's initial cli arguments
        if "--no-window" not in args[0].get_arguments():
            self.activate()

        return 0

    def setup(self, _):
        settings = Settings.load()
        self.hold()  # Keep the app running even without a window

        if settings.show_indicator_icon:
            self.toggle_appindicator(True)

        if FIRST_RUN or settings.hotkey_show_app:
            if HotkeyController.is_supported():
                hotkey = "<Primary>space"
                if settings.hotkey_show_app and not HotkeyController.is_plasma():
                    hotkey = settings.hotkey_show_app
                if HotkeyController.setup_default(hotkey):
                    display_name = Gtk.accelerator_get_label(*Gtk.accelerator_parse(hotkey))
                    body = f'Ulauncher has added a global keyboard shortcut: "{display_name}" to your desktop settings'
                    notification_id = "de_hotkey_auto_created"
                    notification = Gio.Notification.new("Global shortcut created")
                    notification.set_default_action("-")  # Add non-existing action to prevent activating on click
                    notification.set_body(body)

            else:
                notification_id = "de_hotkey_unsupported"
                notification = Gio.Notification.new("Cannot create global shortcut")
                notification.set_default_action("app.show-preferences")
                notification.set_body(
                    "Ulauncher doesn't support setting global keyboard shortcuts for your desktop. "
                    "There are more details on this in the preferences view (click here to open)."
                )

            settings.hotkey_show_app = ""  # Remove json file setting so the notification won't show again
            settings.save()
            notification.set_priority(3)
            self.send_notification(notification_id, notification)

        ExtensionServer.get_instance().start()
        time.sleep(0.01)
        ExtensionRunner.get_instance().run_all()

    def show_launcher(self):
        if not self.window:
            self.window = UlauncherWindow(application=self)
        self.window.show()

    def show_preferences(self, page=None, *_):
        if not isinstance(page, str):
            page = None  # show_preferences is also bound to an event, passing a widget as the first arg
        if self.window:
            self.window.hide()

        if self.preferences:
            self.preferences.present(page)
        else:
            self.preferences = PreferencesWindow(application=self)
            self.preferences.show(page)

    def activate_query(self, _action, variant, *_):
        self.activate()
        self.query = variant.get_string()
