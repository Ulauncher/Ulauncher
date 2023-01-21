from gi.repository import Gio
from ulauncher.utils.Settings import Settings
from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.apps.AppResult import AppResult


class AppMode(BaseMode):
    def get_triggers(self):
        settings = Settings.load()

        for app in Gio.DesktopAppInfo.get_all():
            executable = app.get_executable()
            if not executable or not app.get_display_name():
                continue
            if not app.get_show_in() and not settings.disable_desktop_filters:
                continue
            # Make an exception for gnome-control-center, because all the very useful specific settings
            # like "Keyboard", "Wi-Fi", "Sound" etc have NoDisplay=true
            if app.get_nodisplay() and executable != "gnome-control-center":
                continue
            # Don't show Ulauncher app in own list
            if app.get_id() == "io.ulauncher.Ulauncher.desktop":
                continue

            yield AppResult(app)
