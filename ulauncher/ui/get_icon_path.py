from __future__ import annotations

import logging
from os.path import expanduser

from gi.repository import Gtk

from ulauncher.gi import GLib

icon_theme = Gtk.IconTheme.get_default()
logger = logging.getLogger(__name__)


def get_icon_path(icon: str, size: int = 32) -> str | None:
    try:
        if icon and isinstance(icon, str):
            icon = expanduser(icon)
            if icon.startswith("/"):
                return icon

            if themed_icon := icon_theme.lookup_icon(icon, size, Gtk.IconLookupFlags.FORCE_SIZE):
                return themed_icon.get_filename()

    except GLib.Error as err:
        logger.warning("Error '%s' occurred when trying to load icon path '%s'.", err, icon)
        logger.info("If this happens often, please see https://github.com/Ulauncher/Ulauncher/discussions/1346")

    return None
