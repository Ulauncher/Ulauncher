from typing import cast

import gi
gi.require_version('Gio', '2.0')

# pylint: disable=wrong-import-position
from gi.repository import Gio

"""
A wrapper around Gio.DesktopAppInfo to provide compatibility with breaking change in GLib 2.86.0
"""

try:
    from gi.repository import GioUnix  # type: ignore[attr-defined]
except ImportError:
    GioUnix = Gio


DesktopAppInfo = cast("Gio.DesktopAppInfo", GioUnix.DesktopAppInfo)
