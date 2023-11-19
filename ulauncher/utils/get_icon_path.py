from __future__ import annotations

import logging
import mimetypes
from os.path import expanduser, join

from gi.repository import Gtk

icon_theme = Gtk.IconTheme.get_default()  # type: ignore[attr-defined]
logger = logging.getLogger()


def get_icon_path(icon, size=32, base_path=""):
    """
    :param str icon:
    :rtype: str
    """
    try:
        if icon and isinstance(icon, str):
            icon = expanduser(icon)
            if icon.startswith("/"):
                return icon

            if "/" in icon or mimetypes.guess_type(icon)[0]:
                return join(base_path, icon)

            themed_icon = icon_theme.lookup_icon(icon, size, Gtk.IconLookupFlags.FORCE_SIZE)
            if themed_icon:
                return themed_icon.get_filename()

    except Exception as e:
        logger.info("Could not load icon path %s. E: %s", icon, e)

    return None
