from __future__ import annotations

import logging
from datetime import timedelta
from functools import lru_cache
from os.path import expanduser, isfile, join

from gi.repository import Gtk

from ulauncher.utils.file_cache import file_cache

icon_theme = Gtk.IconTheme.get_default()
logger = logging.getLogger()
get_icon_theme = lru_cache(maxsize=1)(Gtk.IconTheme.get_default)


@file_cache(expiry=timedelta(days=1))
def dummyfn() -> None:
    pass


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
