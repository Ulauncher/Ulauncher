import logging

import gi
from gi.repository import Gio

logger = logging.getLogger()

# Gio/GioUnix aliases were removed in GLib 2.86.0, so we need to add them back

try:
    gi.require_version("GioUnix", "2.0")
    from gi.repository import GioUnix  # type: ignore[attr-defined]

    # Patching more recent versions with GioUnix.* to be compatible with Gio.Unix*
    # I would prefer to do it the other way around, but then I would also have to fight the type stubs.

    if not hasattr(Gio, "UnixInputStream") and hasattr(GioUnix, "InputStream"):
        Gio.UnixInputStream = GioUnix.InputStream  # type: ignore[misc]

    if not hasattr(Gio, "UnixOutputStream") and hasattr(GioUnix, "OutputStream"):
        Gio.UnixOutputStream = GioUnix.OutputStream  # type: ignore[misc]

except (ImportError, ValueError):
    if hasattr(Gio, "UnixInputStream") or not hasattr(Gio, "UnixOutputStream"):
        logger.warning("Failed to patch GioUnix methods")
