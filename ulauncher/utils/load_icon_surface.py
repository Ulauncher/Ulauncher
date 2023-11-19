from __future__ import annotations

import logging
from functools import lru_cache

from gi.repository import Gdk, GdkPixbuf

import ulauncher
from ulauncher.utils.get_icon_path import get_icon_path

logger = logging.getLogger()

DEFAULT_EXE_ICON = f"{ulauncher.data_dir}/icons/executable.png"


@lru_cache(maxsize=50)
def load_icon_surface(icon, size, scaling_factor=1):
    """
    :param str icon:
    :param int size:
    :rtype: :class:`GtkPixbuf`
    """
    real_size = size * scaling_factor
    try:
        icon_path = get_icon_path(icon, real_size) or DEFAULT_EXE_ICON
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, real_size, real_size)
        return Gdk.cairo_surface_create_from_pixbuf(pixbuf, scaling_factor)
    except Exception as e:
        if icon_path == DEFAULT_EXE_ICON:
            msg = f"Could not load fallback icon: {icon_path}"
            raise RuntimeError(msg) from e

        logger.warning("Could not load specified icon %s (%s). Will use fallback icon", icon, e)
        return load_icon_surface(DEFAULT_EXE_ICON, size, scaling_factor)
