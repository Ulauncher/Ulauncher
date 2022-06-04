import gi

gi.require_version('Gtk', '3.0')

# AppIndicator support is optional. It'll work if you install
# gir1.2-ayatanaappindicator3-0.1 or an equivalent package for your distro
# pylint: disable=wrong-import-position
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
except (ImportError, ValueError):
    try:
        gi.require_version('AyatanaAppIndicator3', '0.1')
        from gi.repository import AyatanaAppIndicator3 as AppIndicator3  # noqa: F811
    except (ImportError, ValueError):
        AppIndicator3 = None

from gi.repository import Gtk


def create_menu_item(title, command):
    menu_item = Gtk.MenuItem(title)
    menu_item.connect("activate", command)
    return menu_item


class AppIndicator:
    menu = Gtk.Menu()
    indicator = None

    def __init__(self, app):
        if AppIndicator3:
            self.menu.append(create_menu_item("Preferences", lambda *_: app.show_preferences()))
            self.menu.append(create_menu_item("About", lambda *_: app.show_preferences("about")))
            self.menu.append(Gtk.SeparatorMenuItem())
            self.menu.append(create_menu_item("Exit", lambda *_: app.quit()))
            self.menu.show_all()
            self.indicator = AppIndicator3.Indicator.new(
                "ulauncher",
                "ulauncher-indicator",
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
            self.indicator.set_menu(self.menu)

    def switch(self, enable=False):
        if AppIndicator3:
            status = getattr(AppIndicator3.IndicatorStatus, "ACTIVE" if enable else "PASSIVE")
            self.indicator.set_status(status)
