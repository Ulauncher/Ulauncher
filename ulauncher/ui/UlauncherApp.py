import time
import logging
from functools import lru_cache
from typing import Optional
from gi.repository import Gio, GLib, Gtk, Keybinder  # type: ignore[attr-defined]
from ulauncher.config import FIRST_RUN
from ulauncher.utils.environment import IS_X11
from ulauncher.utils.Settings import Settings
from ulauncher.utils.desktop.notification import show_notification
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.ui.windows.PreferencesWindow import PreferencesWindow
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
from ulauncher.modes.extensions.ExtensionRunner import ExtensionRunner
from ulauncher.modes.extensions.ExtensionServer import ExtensionServer
from ulauncher.api.shared.query import Query

logger = logging.getLogger()


class UlauncherApp(Gtk.Application):
    """
    Main Ulauncher application (singleton)
    """

    # Gtk.Applications check if the app is already registered and if so,
    # new instances sends the signals to the registered one
    # So all methods except __init__ runs on the main app
    _query = ""
    window: Optional[UlauncherWindow] = None
    preferences: Optional[PreferencesWindow] = None
    _appindicator: Optional[AppIndicator] = None
    _current_accel_name = None

    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls):
        return cls()

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, application_id="io.ulauncher.Ulauncher", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs
        )
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

    def do_before_emit(self, *args, **kwargs):
        query = args[0].lookup_value("query", GLib.VariantType("s"))
        if query:
            self.query = query.unpack()

    def do_activate(self, *args, **kwargs):
        self.window.show()

    def do_command_line(self, *args, **kwargs):
        # We need to use "--no-window" from the unique CLI invocation here,
        # Can't use config.get_options(), because that's the daemon's initial cli arguments
        if "--no-window" not in args[0].get_arguments():
            self.activate()

        return 0

    def setup(self, _):
        settings = Settings.load()
        self.hold()  # Keep the app running even without a window
        self.window = UlauncherWindow()
        self.window.set_application(self)
        self.window.set_keep_above(True)
        self.window.position_window()
        self.window.apply_theme()

        # this will trigger to show frequent apps if necessary
        self.window.show_results([])

        if settings.show_indicator_icon:
            self.toggle_appindicator(True)

        if IS_X11:
            # bind hotkey
            Keybinder.init()
            # bind in the main thread
            GLib.idle_add(self.bind_hotkey, settings.hotkey_show_app)

        ExtensionServer.get_instance().start()
        time.sleep(0.01)
        ExtensionRunner.get_instance().run_all()

    def toggle_appindicator(self, enable):
        if not self._appindicator:
            self._appindicator = AppIndicator(self)
        self._appindicator.switch(enable)

    def bind_hotkey(self, accel_name):
        if not IS_X11 or self._current_accel_name == accel_name:
            return

        if self._current_accel_name:
            Keybinder.unbind(self._current_accel_name)
            self._current_accel_name = None

        logger.info("Trying to bind app hotkey: %s", accel_name)
        Keybinder.bind(accel_name, lambda _: self.window.show())
        self._current_accel_name = accel_name
        if FIRST_RUN:
            display_name = Gtk.accelerator_get_label(*Gtk.accelerator_parse(accel_name))
            show_notification("Ulauncher", f"Hotkey is set to {display_name}")

    def show_preferences(self, page=None):
        self.window.hide()

        if self.preferences:
            self.preferences.present(page)
        else:
            self.preferences = PreferencesWindow(application=self)
            self.preferences.show(page)
