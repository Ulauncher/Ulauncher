import logging

import gi
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk, AppIndicator3
from ulauncher.util.decorator.singleton import singleton

logger = logging.getLogger(__name__)


class AppIndicator(object):

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
        self.__menu = Gtk.Menu()
        self.__indicator = AppIndicator3.Indicator.new(iconname, "", AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.__indicator.set_menu(self.__menu)

    def set_icon(self, path):
        self.__indicator.set_icon(path)

    def switch(self, on=False):
        self.show() if on else self.hide()

    def add_menu_item(self, command, title):
        menu_item = Gtk.MenuItem()
        menu_item.set_label(title)
        menu_item.connect("activate", command)
        self.__menu.append(menu_item)

    def add_seperator(self):
        menu_item = Gtk.SeparatorMenuItem()
        self.__menu.append(menu_item)

    def show(self):
        self.__indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.__menu.show_all()

    def hide(self):
        self.__indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

    def get_tray_menu(self):
        return self.__menu

    def right_click_event_statusicon(self, icon, button, time):
        self.get_tray_menu()

        def pos(menu, aicon):
            return Gtk.StatusIcon.position_menu(menu, aicon)

        self.__menu.popup(None, None, pos, icon, button, time)
