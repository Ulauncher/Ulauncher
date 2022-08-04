import time
import argparse
import logging
from gi.repository import Gio, GLib, Gtk, Keybinder
from ulauncher.config import FIRST_RUN
from ulauncher.utils.environment import IS_X11
from ulauncher.utils.Settings import Settings
from ulauncher.utils.desktop.notification import show_notification
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.ui.windows.PreferencesWindow import PreferencesWindow
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
from ulauncher.modes.extensions.ExtensionRunner import ExtensionRunner
from ulauncher.modes.extensions.ExtensionServer import ExtensionServer

logger = logging.getLogger()


class UlauncherApp(Gtk.Application):
    # Gtk.Applications check if the app is already registered and if so,
    # new instances sends the signals to the registered one
    # So all methods except __init__ runs on the main app
    settings = Settings.load()
    window = None  # type: UlauncherWindow
    preferences = None  # type: PreferencesWindow
    appindicator = None  # type: AppIndicator
    _current_accel_name = None

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="net.launchpad.ulauncher",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )
        self.connect("startup", self.setup)  # runs only once on the main instance

    def do_before_emit(self, *args, **kwargs):
        query = args[0].lookup_value("query", GLib.VariantType("s"))
        if query:
            self.window.initial_query = query.unpack()

    def do_activate(self, *args, **kwargs):
        self.window.show_window()

    def do_command_line(self, *args, **kwargs):
        # This is where we handle "--no-window" which we need to get from the remote call
        # All other aguments are persistent and handled in config.get_options()
        parser = argparse.ArgumentParser(prog='gui')
        parser.add_argument("--no-window", action="store_true")
        args, _ = parser.parse_known_args(args[0].get_arguments()[1:])

        if not args.no_window:
            self.activate()

        return 0

    def setup(self, _):
        self.hold()  # Keep the app running even without a window
        self.window = window = UlauncherWindow.get_instance()
        window.set_application(self)
        window.set_keep_above(True)
        window.position_window()
        window.init_theme()

        # this will trigger to show frequent apps if necessary
        window.show_results([])

        if self.settings.show_indicator_icon:
            self.appindicator = AppIndicator(self)
            self.appindicator.switch(True)

        if IS_X11:
            # bind hotkey
            Keybinder.init()
            # bind in the main thread
            GLib.idle_add(self.bind_hotkey, self.settings.hotkey_show_app)

        ExtensionServer.get_instance().start()
        time.sleep(0.01)
        ExtensionRunner.get_instance().run_all()

    def toggle_appindicator(self, enable):
        if not self.appindicator:
            self.appindicator = AppIndicator(self)
        self.appindicator.switch(enable)

    def bind_hotkey(self, accel_name):
        if not IS_X11 or self._current_accel_name == accel_name:
            return

        if self._current_accel_name:
            Keybinder.unbind(self._current_accel_name)
            self._current_accel_name = None

        logger.info("Trying to bind app hotkey: %s", accel_name)
        Keybinder.bind(accel_name, lambda _: self.window.show_window())
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
