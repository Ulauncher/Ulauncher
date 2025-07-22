from __future__ import annotations

import logging
from functools import lru_cache

from cairo import ImageSurface
from gi.repository import Gdk, GdkPixbuf

from ulauncher import paths

logger = logging.getLogger()

DEFAULT_EXE_ICON = f"{paths.ASSETS}/icons/executable.png"


@lru_cache(maxsize=50)
def load_icon_surface(icon: str, size: int, scaling_factor: int = 1) -> ImageSurface:
    real_size = size * scaling_factor
    try:
        if not icon.startswith("/"):
            from ulauncher.utils.get_icon_path import get_icon_path

            icon = get_icon_path(icon, real_size) or DEFAULT_EXE_ICON
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, real_size, real_size)
        assert pixbuf
        return Gdk.cairo_surface_create_from_pixbuf(pixbuf, scaling_factor)
    except Exception as e:
        if icon == DEFAULT_EXE_ICON:
            msg = f"Could not load fallback icon: {icon}"
            raise RuntimeError(msg) from e

        logger.warning("Could not load specified icon %s (%s). Will use fallback icon", icon, e)
        return load_icon_surface(DEFAULT_EXE_ICON, size, scaling_factor)
