import logging
import mimetypes
from os.path import expanduser, join
from functools import lru_cache
from gi.repository import Gdk, Gtk, GdkPixbuf
from ulauncher import ASSETS

icon_theme = Gtk.IconTheme.get_default()  # type: ignore[attr-defined]
logger = logging.getLogger()

DEFAULT_EXE_ICON = f"{ASSETS}/icons/executable.png"


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
            raise RuntimeError(f"Could not load fallback icon: {icon_path}") from e

        logger.warning("Could not load specified icon %s (%s). Will use fallback icon", icon, e)
        return load_icon_surface(DEFAULT_EXE_ICON, size, scaling_factor)
