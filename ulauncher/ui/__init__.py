from __future__ import annotations

import logging
from functools import lru_cache
from os.path import expanduser, isfile, join
from typing import TYPE_CHECKING, Iterator

from ulauncher import paths
from ulauncher.gi import Gio, GLib

if TYPE_CHECKING:
    from cairo import ImageSurface  # pyrefly: ignore - this fails in our docker image for some reason

    from ulauncher.gi import Gdk


DEFAULT_EXE_ICON = f"{paths.ASSETS}/icons/executable.png"
logger = logging.getLogger()


def get_monitor(use_mouse_position: bool = False) -> Gdk.Monitor | None:
    from ulauncher.gi import Gdk, GdkX11

    display = Gdk.Display.get_default()
    if not display:
        logger.warning("Could not get default display")
        return None

    if use_mouse_position:
        if (
            (x11_display := GdkX11.X11Display.get_default())
            and (seat := x11_display.get_default_seat())
            and (pointer := seat.get_pointer())
        ):
            (_, x, y) = pointer.get_position()
            return display.get_monitor_at_point(x, y)
        logger.info("Could not get monitor with X11. Defaulting to first or primary monitor")

    return display.get_primary_monitor() or display.get_monitor(0)


def get_text_scaling_factor() -> float:
    # GTK seems to already compensate for monitor scaling, so this just returns font scaling
    # GTK doesn't seem to allow different scaling factors on different displays
    # Text_scaling allow fractional scaling

    return Gio.Settings.new("org.gnome.desktop.interface").get_double("text-scaling-factor")


def get_icon_path(icon: str, size: int = 32, base_path: str = "") -> str | None:
    try:
        if icon and isinstance(icon, str):
            icon = expanduser(icon)
            if icon.startswith("/"):
                return icon

            expanded_path = join(base_path, icon)
            if isfile(expanded_path):
                return expanded_path

            from ulauncher.gi import Gtk

            if themed_icon := Gtk.IconTheme.get_default().lookup_icon(icon, size, Gtk.IconLookupFlags.FORCE_SIZE):
                return themed_icon.get_filename()

    except (OSError, GLib.Error) as err:
        logger.warning("Error '%s' occurred when trying to load icon path '%s'.", err, icon)
        logger.info("If this happens often, please see https://github.com/Ulauncher/Ulauncher/discussions/1346")

    return None


@lru_cache(maxsize=50)
def load_icon_surface(icon: str, size: int, scaling_factor: int = 1) -> ImageSurface:
    from ulauncher.gi import Gdk, GdkPixbuf

    real_size = size * scaling_factor
    try:
        if not icon.startswith("/"):
            icon = get_icon_path(icon, real_size) or DEFAULT_EXE_ICON
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, real_size, real_size)
        if not pixbuf:
            msg = f"Could not load icon pixbuf: {icon}"
            raise RuntimeError(msg)
        return Gdk.cairo_surface_create_from_pixbuf(pixbuf, scaling_factor)
    except GLib.Error as e:
        if icon == DEFAULT_EXE_ICON:
            msg = f"Could not load fallback icon: {icon}"
            raise RuntimeError(msg) from e

        logger.warning("Could not load specified icon %s (%s). Will use fallback icon", icon, e)
        return load_icon_surface(DEFAULT_EXE_ICON, size, scaling_factor)


def highlight_text(query_str: str, text: str) -> Iterator[tuple[str, bool]]:
    from ulauncher.utils.fuzzy_search import get_matching_blocks

    block_index = 0
    for index, chars in get_matching_blocks(query_str, text)[0]:
        chars_len = len(chars)
        if index != block_index:
            yield (text[block_index:index], False)
        yield (chars, True)
        block_index = index + chars_len
    if block_index < len(text):
        yield (text[block_index:], False)
