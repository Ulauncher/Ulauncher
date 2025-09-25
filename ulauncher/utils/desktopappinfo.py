from typing import cast

import gi
from gi.repository import Gio

try:
    gi.require_version("GioUnix", "2.0")
    from gi.repository import GioUnix  # type: ignore[attr-defined]
except (ImportError, ValueError):
    GioUnix = Gio


DesktopAppInfo = cast("Gio.DesktopAppInfo", GioUnix.DesktopAppInfo)
