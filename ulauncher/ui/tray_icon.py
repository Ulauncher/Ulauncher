# Status icon support is optional. It'll work if you install XApp or AppIndicator3
# Only XApp supports activating the launcher on left click and showing the menu on right click

from __future__ import annotations

import contextlib
import logging
from pathlib import Path
from typing import Any, Callable, Literal

import gi
from gi.repository import GObject, Gtk

from ulauncher import paths
from ulauncher.utils.environment import IS_X11_COMPATIBLE
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.settings import Settings

tray_icon_lib: Literal["AyatanaIndicator", "XApp"] | None = None
logger = logging.getLogger()
events = EventBus()
icon_asset_path = f"{paths.ASSETS}/icons/system/status"
default_icon_name = Settings.tray_icon_name  # intentionally using the class, not the instance, to get the default


if IS_X11_COMPATIBLE:
    with contextlib.suppress(ImportError, ValueError):
        gi.require_version("XApp", "1.0")
        from gi.repository import XApp

        # Older versions of XApp doesn't have StatusIcon
        if hasattr(XApp, "StatusIcon"):
            tray_icon_lib = "XApp"

if tray_icon_lib is None:
    try:
        gi.require_version("AppIndicator3", "0.1")
        from gi.repository import AppIndicator3 as AyatanaIndicator

        tray_icon_lib = "AyatanaIndicator"

    except (ImportError, ValueError):
        with contextlib.suppress(ImportError, ValueError):
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3 as AyatanaIndicator  # type: ignore[no-redef]

            tray_icon_lib = "AyatanaIndicator"


def _create_menu_item(label: str, handler: Callable[[Any], None]) -> Gtk.MenuItem:
    menu_item = Gtk.MenuItem(label=label)
    menu_item.connect("activate", handler)
    return menu_item


class TrayIcon(GObject.Object):
    _indicator: Any | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        menu = Gtk.Menu()
        show_menu_item: Gtk.MenuItem | None = None
        if self.supports_appindicator():
            show_menu_item = _create_menu_item("Show Ulauncher", lambda *_: events.emit("app:show_launcher"))
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

        if tray_icon_lib == "XApp":
            if icon_dir:
                # Xapp supports loading from path instead of icon name
                icon_name = f"{icon_dir}/{icon_name}.svg"

            self.xapp_indicator = XApp.StatusIcon()
            self.xapp_indicator.set_icon_name(icon_name)
            # Show menu on right click and show launcher on left click
            self.xapp_indicator.set_secondary_menu(menu)
            self.xapp_indicator.connect("activate", lambda *_: events.emit("app:show_launcher"))

        elif tray_icon_lib == "AyatanaIndicator":
            app_status = AyatanaIndicator.IndicatorCategory.APPLICATION_STATUS
            self.aya_indicator = AyatanaIndicator.Indicator.new("ulauncher", icon_name, app_status)
            if icon_dir:
                self.aya_indicator.set_icon_theme_path(icon_dir)

            # libappindicator can't / won't distinguish between left and right clicks
            # Show menu on left or right click and show launcher on middle click
            self.aya_indicator.set_menu(menu)
            self.aya_indicator.set_secondary_activate_target(show_menu_item)

    def supports_appindicator(self) -> bool:
        return bool(tray_icon_lib)

    def switch(self, status: bool = False) -> None:
        if tray_icon_lib == "XApp":
            self.xapp_indicator.set_visible(status)
        elif tray_icon_lib == "AyatanaIndicator":
            aya_status = getattr(AyatanaIndicator.IndicatorStatus, "ACTIVE" if status else "PASSIVE")
            self.aya_indicator.set_status(aya_status)
