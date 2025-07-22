# Ignore type errors for the TrayIcon deps
# mypy: disable-error-code="attr-defined"
import logging
from pathlib import Path
from typing import Any, Callable

import gi
from gi.repository import GObject, Gtk

from ulauncher.utils.eventbus import EventBus

# Status icon support is optional. It'll work if you install XApp or AppIndicator3
# Only XApp supports activating the launcher on left click and showing the menu on right click
try:
    gi.require_version("XApp", "1.0")
    from gi.repository import XApp

    # Older versions of XApp doesn't have StatusIcon
    assert hasattr(XApp, "StatusIcon")
    AyatanaIndicator = None
except (AssertionError, ImportError, ValueError):
    XApp = None  # type: ignore[assignment, unused-ignore]
    try:
        gi.require_version("AppIndicator3", "0.1")
        from gi.repository import AppIndicator3

        AyatanaIndicator = AppIndicator3
    except (ImportError, ValueError):
        try:
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3

            AyatanaIndicator = AyatanaAppIndicator3
        except (ImportError, ValueError):
            AyatanaIndicator = None

from ulauncher import paths
from ulauncher.utils.settings import Settings

logger = logging.getLogger()
events = EventBus()
icon_asset_path = f"{paths.ASSETS}/icons/system/status"
default_icon_name = Settings.tray_icon_name  # intentionally using the class, not the instance, to get the default


def _create_menu_item(label: str, handler: Callable[[Any], None]) -> Gtk.MenuItem:
    menu_item = Gtk.MenuItem(label=label)
    menu_item.connect("activate", handler)
    return menu_item


class TrayIcon(GObject.Object):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.supports_appindicator():
            show_menu_item = _create_menu_item("Show Ulauncher", lambda *_: events.emit("app:show_launcher"))
            menu = Gtk.Menu()
            menu.append(show_menu_item)
            menu.append(_create_menu_item("Preferences", lambda *_: events.emit("app:show_preferences")))
            menu.append(_create_menu_item("About", lambda *_: events.emit("app:show_preferences", "about")))
            menu.append(Gtk.SeparatorMenuItem())
            menu.append(_create_menu_item("Exit", lambda *_: events.emit("app:quit")))
            menu.show_all()

        gtk_icon_theme = Gtk.IconTheme.get_default()
        icon_name = "find"  # standard find icon, in case the app is not installed
        icon_dir = ""
        icons = list({Settings.load().tray_icon_name, default_icon_name, "ulauncher-indicator"})

        # check preferred, fallback on default v6 icon name, then the v5 icon name if v5 is installed
        for _icon in icons:
            # check installed icon
            if gtk_icon_theme.has_icon(_icon):
                icon_name = _icon
                break
            # check asset dir icon
            if Path(f"{icon_asset_path}/{_icon}.svg").is_file():
                icon_name = _icon
                icon_dir = icon_asset_path
                break
            logger.warning("Could not find Ulauncher icon %s", _icon)

        if XApp:
            if icon_dir:
                # Xapp supports loading from path instead of icon name
                icon_name = f"{icon_dir}/{icon_name}.svg"

            self._indicator = XApp.StatusIcon()
            self._indicator.set_icon_name(icon_name)
            # Show menu on right click and show launcher on left click
            self._indicator.set_secondary_menu(menu)
            self._indicator.connect("activate", lambda *_: events.emit("app:show_launcher"))

        elif AyatanaIndicator:
            if icon_dir:
                self._indicator = AyatanaIndicator.Indicator.new_with_path(
                    "ulauncher", icon_name, AyatanaIndicator.IndicatorCategory.APPLICATION_STATUS, icon_dir
                )
            else:
                self._indicator = AyatanaIndicator.Indicator.new(
                    "ulauncher", icon_name, AyatanaIndicator.IndicatorCategory.APPLICATION_STATUS
                )
            # libappindicator can't / won't distinguish between left and right clicks
            # Show menu on left or right click and show launcher on middle click
            self._indicator.set_menu(menu)
            self._indicator.set_secondary_activate_target(show_menu_item)

    def supports_appindicator(self) -> bool:
        return bool(XApp or AyatanaIndicator)

    def switch(self, status: bool = False) -> None:
        if XApp:
            self._indicator.set_visible(status)
        elif AyatanaIndicator:
            status = getattr(AyatanaIndicator.IndicatorStatus, "ACTIVE" if status else "PASSIVE")
            self._indicator.set_status(status)
