from functools import wraps
import logging

import gi
gi.require_version('Gtk', '3.0')

# AppIndicator support is optional. It'll work if you install
# gir1.2-ayatanaappindicator3-0.1 or an equivalent package for your distro
# pylint: disable=wrong-import-position,import-outside-toplevel
appIndicatorSupported = False
try:
    gi.require_version('AppIndicator3', '0.1')
    appIndicatorSupported = True
except ValueError:
    pass

try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    appIndicatorSupported = True
except ValueError:
    pass

try:
    from gi.repository import AppIndicator3
except ImportError:
    pass

try:
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3  # noqa: F811
except ImportError:
    pass

from gi.repository import Gtk
from ulauncher.utils.decorator.singleton import singleton

logger = logging.getLogger(__name__)


def onlyIfAppindicatorIsSupported(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if appIndicatorSupported:
            return func(*args, **kwargs)
        return None
    return wrapped


class AppIndicator:

    @classmethod
    @singleton
    def get_instance(cls):
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        window = UlauncherWindow.get_instance()
        indicator = cls("ulauncher")
        indicator.set_icon('ulauncher-indicator')
        indicator.add_menu_item(window.on_mnu_preferences_activate, "Preferences")
        indicator.add_menu_item(window.on_mnu_about_activate, "About")
        indicator.add_seperator()
        indicator.add_menu_item(Gtk.main_quit, "Exit")
        return indicator

    def __init__(self, iconname):
        if appIndicatorSupported:
            self.__menu = Gtk.Menu()
            self.__indicator = AppIndicator3.Indicator.new(
                iconname,
                "",
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
            self.__indicator.set_menu(self.__menu)

    @onlyIfAppindicatorIsSupported
    def set_icon(self, path):
        self.__indicator.set_icon(path)

    @onlyIfAppindicatorIsSupported
    def switch(self, on=False):
        if on:
            self.show()
        else:
            self.hide()

    @onlyIfAppindicatorIsSupported
    def add_menu_item(self, command, title):
        menu_item = Gtk.MenuItem()
        menu_item.set_label(title)
        menu_item.connect("activate", command)
        self.__menu.append(menu_item)

    @onlyIfAppindicatorIsSupported
    def add_seperator(self):
        menu_item = Gtk.SeparatorMenuItem()
        self.__menu.append(menu_item)

    @onlyIfAppindicatorIsSupported
    def show(self):
        self.__indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.__menu.show_all()

    @onlyIfAppindicatorIsSupported
    def hide(self):
        self.__indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

    @onlyIfAppindicatorIsSupported
    def right_click_event_statusicon(self, icon, button, time):
        self._get_tray_menu()

        def pos(menu, aicon):
            return Gtk.StatusIcon.position_menu(menu, aicon)

        self.__menu.popup(None, None, pos, icon, button, time)

    def _get_tray_menu(self):
        return self.__menu
