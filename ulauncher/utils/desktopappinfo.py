from typing import cast

from gi.repository import Gio

try:
    from gi.repository import GioUnix  # type: ignore[attr-defined]
except ImportError:
    GioUnix = Gio


DesktopAppInfo = cast("Gio.DesktopAppInfo", GioUnix.DesktopAppInfo)
