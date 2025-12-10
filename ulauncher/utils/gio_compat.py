import contextlib
import logging
from typing import Any

import gi
from gi.repository import Gio

logger = logging.getLogger()
GioUnix: Any = None

# Gio/GioUnix aliases were removed in GLib 2.86.0, so we need to patch them back
# Since the type stubs only has the legacy types and not the new GioUnix, we have to patch the legacy Gio
# I would prefer to do it the other way around, but I don't want to fight the type system.

with contextlib.suppress(ImportError, ValueError):
    gi.require_version("GioUnix", "2.0")
    from gi.repository import GioUnix  # type: ignore[no-redef, attr-defined]


if not hasattr(Gio, "UnixInputStream"):
    if hasattr(GioUnix, "InputStream"):
        Gio.UnixInputStream = GioUnix.InputStream  # type: ignore[misc]
    else:
        err_msg = "Neither GioUnix.InputStream or Gio.UnixInputStream could be found"
        raise ImportError(err_msg)

if not hasattr(Gio, "UnixOutputStream"):
    if hasattr(GioUnix, "OutputStream"):
        Gio.UnixOutputStream = GioUnix.OutputStream  # type: ignore[misc]
    else:
        err_msg = "Neither GioUnix.OutputStream or Gio.UnixOutputStream could be found"
        raise ImportError(err_msg)
