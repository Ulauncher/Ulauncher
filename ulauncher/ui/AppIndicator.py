import logging

import gi
from gi.repository import Gio, Gtk

# Status icon support is optional. It'll work if you install XApp or AppIndicator3
# Only XApp supports activating the launcher on left click and showing the menu on right click
try:
    gi.require_version("XApp", "1.0")
    from gi.repository import XApp  # type: ignore[attr-defined]

    # Older versions of XApp doesn't have StatusIcon
    assert hasattr(XApp, "StatusIcon")
    AyatanaIndicator = None
except (AssertionError, ImportError, ValueError):
    XApp = None
    try:
        gi.require_version("AppIndicator3", "0.1")
        from gi.repository import AppIndicator3  # type: ignore[attr-defined]

        AyatanaIndicator = AppIndicator3
    except (ImportError, ValueError):
        try:
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3

            AyatanaIndicator = AyatanaAppIndicator3
        except (ImportError, ValueError):
            AyatanaIndicator = None

from ulauncher.utils.Settings import Settings

logger = logging.getLogger()


def _create_menu_item(label, command):
    menu_item = Gtk.MenuItem(label=label)
    menu_item.connect("activate", command)
    return menu_item


class AppIndicator(Gio.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.supports_appindicator():
            show_menu_item = _create_menu_item("Show Ulauncher", lambda *_: self.activate())
            menu = Gtk.Menu()
            menu.append(show_menu_item)
            menu.append(_create_menu_item("Preferences", lambda *_: self.show_preferences()))
            menu.append(_create_menu_item("About", lambda *_: self.show_preferences("about")))
            menu.append(Gtk.SeparatorMenuItem())
            menu.append(_create_menu_item("Exit", lambda *_: self.quit()))
            menu.show_all()

        gtk_icon_theme = Gtk.IconTheme.get_default()
        icon_name = "find"  # standard find icon, in case the app is not installed

        # check preferred, fallback on default v6 icon name, then the v5 icon name if v5 is installed
        for _icon in list({Settings.load().status_icon_name, "ulauncher-indicator-symbolic", "ulauncher-indicator"}):
            if gtk_icon_theme.has_icon(_icon):
                icon_name = _icon
                break
            logger.warning("Could not find Ulauncher icon %s", _icon)

        if XApp:
            self._indicator = XApp.StatusIcon()
            self._indicator.set_icon_name(icon_name)
            # Show menu on right click and show launcher on left click
            self._indicator.set_secondary_menu(menu)
            self._indicator.connect("activate", lambda *_: self.activate())

        elif AyatanaIndicator:
            self._indicator = AyatanaIndicator.Indicator.new(
                "ulauncher", icon_name, AyatanaIndicator.IndicatorCategory.APPLICATION_STATUS
            )
            # libappindicator can't / won't distinguish between left and right clicks
            # Show menu on left or right click and show launcher on middle click
            self._indicator.set_menu(menu)
            self._indicator.set_secondary_activate_target(show_menu_item)

    def supports_appindicator(self):
        return bool(XApp or AyatanaIndicator)

    def toggle_appindicator(self, status=False):
        if XApp:
            self._indicator.set_visible(status)
        elif AyatanaIndicator:
            self._indicator.set_status(getattr(AyatanaIndicator.IndicatorStatus, "ACTIVE" if status else "PASSIVE"))

    # dummy method, we override it in UlauncherApp
    def show_preferences(self, page=None):
        pass
