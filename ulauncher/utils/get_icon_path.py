from __future__ import annotations

import logging
from os.path import expanduser, isfile, join

from gi.repository import Gtk

icon_theme = Gtk.IconTheme.get_default()  # type: ignore[attr-defined]
logger = logging.getLogger()


def get_icon_path(icon: str, size: int = 32, base_path: str = "") -> str | None:
    """
    :param str icon:
    :rtype: str
    """
    try:
        if icon and isinstance(icon, str):
            icon = expanduser(icon)
            if icon.startswith("/"):
                return icon

            expanded_path = join(base_path, icon)
            if isfile(expanded_path):
                return expanded_path

            themed_icon = icon_theme.lookup_icon(icon, size, Gtk.IconLookupFlags.FORCE_SIZE)
            if themed_icon:
                return themed_icon.get_filename()

    except Exception as e:
        logger.info("Could not load icon path %s. E: %s", icon, e)

    return None
