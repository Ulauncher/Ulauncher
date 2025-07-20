from __future__ import annotations

import logging
from os.path import expanduser, isfile, join

from gi.repository import Gtk

icon_theme = Gtk.IconTheme.get_default()
logger = logging.getLogger()


def get_icon_path(icon: str, size: int = 32, base_path: str = "") -> str | None:
    try:
        if icon and isinstance(icon, str):
            icon = expanduser(icon)
            if icon.startswith("/"):
                return icon

            expanded_path = join(base_path, icon)
            if isfile(expanded_path):
                return expanded_path

            if themed_icon := icon_theme.lookup_icon(icon, size, Gtk.IconLookupFlags.FORCE_SIZE):
                return themed_icon.get_filename()

    except Exception as err:  # noqa: BLE001
        logger.warning("Error '%s' occurred when trying to load icon path '%s'.", err, icon)
        logger.info("If this happens often, please see https://github.com/Ulauncher/Ulauncher/discussions/1346")

    return None
