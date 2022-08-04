import gi

# Status icon support is optional. It'll work if you install XApp or AppIndicator3
# Only XApp supports activating the launcher on left click and showing the menu on right click
# pylint: disable=wrong-import-position
try:
    gi.require_version('XApp', '1.0')
    from gi.repository import XApp
    # Older versions of XApp doesn't have StatusIcon
    assert hasattr(XApp, 'StatusIcon')
    AyatanaIndicator = None
except (AssertionError, ImportError, ValueError):
    XApp = None
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3
        AyatanaIndicator = AppIndicator3
    except (ImportError, ValueError):
        try:
            gi.require_version('AyatanaAppIndicator3', '0.1')
            from gi.repository import AyatanaAppIndicator3 as AppIndicator3  # noqa: F811
            AyatanaIndicator = AppIndicator3
        except (ImportError, ValueError):
            pass

from gi.repository import GObject, Gtk


def create_menu_item(label, command):
    menu_item = Gtk.MenuItem(label=label)
    menu_item.connect("activate", command)
    return menu_item


class AppIndicator(GObject.Object):
    def __init__(self, app):
        if XApp or AyatanaIndicator:
            show_menu_item = create_menu_item("Show Ulauncher", lambda *_: app.do_activate())
            menu = Gtk.Menu()
            menu.append(show_menu_item)
            menu.append(create_menu_item("Preferences", lambda *_: app.show_preferences()))
            menu.append(create_menu_item("About", lambda *_: app.show_preferences("about")))
            menu.append(Gtk.SeparatorMenuItem())
            menu.append(create_menu_item("Exit", lambda *_: app.quit()))
            menu.show_all()

        if XApp:
            self.indicator = XApp.StatusIcon()
            self.indicator.set_icon_name("ulauncher-indicator")
            # Show menu on right click and show launcher on left click
            self.indicator.set_secondary_menu(menu)
            self.indicator.connect("activate", lambda *_: app.do_activate())

        elif AyatanaIndicator:
            self.indicator = AyatanaIndicator.Indicator.new(
                "ulauncher",
                "ulauncher-indicator",
                AyatanaIndicator.IndicatorCategory.APPLICATION_STATUS
            )
            # libappindicator can't/won't distinguish between left and right clicks
            # Show menu on left or right click and show launcher on middle click
            self.indicator.set_menu(menu)
            self.indicator.set_secondary_activate_target(show_menu_item)

    def switch(self, status=False):
        if XApp:
            self.indicator.set_visible(status)
        elif AyatanaIndicator:
            self.indicator.set_status(getattr(AyatanaIndicator.IndicatorStatus, "ACTIVE" if status else "PASSIVE"))
