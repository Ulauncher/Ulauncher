from __future__ import annotations

import contextlib
import types
import warnings

import gi
from gi.repository import Gio

__all__ = ["GioUnix"]

# 🐛 GioUnix/PyGObject history:
#
# * GioUnix was originally a namespace for aliases to Unix-specific functionality in the Gio namespace.
#
# * GLib 2.84.0 (2025-03-06) created a dedicated GioUnix namespace and moved all the
#   Unix-specific symbols here, while adding aliases in Gio instead for backwards compatibility.
#
# * GLib 2.86.0 (2025-09-05) removed the GioUnix aliases from Gio (breaking PyGObject):
#   https://download.gnome.org/sources/glib/2.86/glib-2.86.0.news
#   https://gitlab.gnome.org/GNOME/glib/-/merge_requests/4761
#
# * PyGObject 3.54.0 (2025-09-06) added partially broken aliases back, to support GLib 2.86.0+
#   https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/445
#
# * PyGObject 3.54.3 (2025-09-21) fixed a problem where wrappers like UnixInputStream were incorrectly skipped
#   https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/452
#
# * PyGObject 3.55.0 (2025-11-15) fixed methods being unbound when using PyGObject 3.54.x with GLib 2.84.x
#   https://gitlab.gnome.org/GNOME/pygobject/-/issues/719
#   https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/456
#
# * pygobject-stubs 2.17.0 (2026-03-20) added stubs for the GioUnix symbols (Py3.10+)
#   This only affects the dev experience and code, and we control the pygobject-stubs version ourselves
#   https://github.com/pygobject/pygobject-stubs/commit/77c45521194ec9ffc280958e5c22e95d8bb1539f
#   https://github.com/pygobject/pygobject-stubs/compare/v2.16.0...v2.17.0
#
# Which means we need to handle all of these cases:
# - GioUnix missing entirely
# - GioUnix imports, but a symbols are missing
# - GioUnix imports, but older GLib with PyGObject 3.54.x still gives unbound methods
# - PyGObject 3.55.0+ should be safe to use with all versions of GLib


class _GioUnixCompat(types.SimpleNamespace):
    """
    Lightweight namespace mimicking GioUnix for the symbols Ulauncher uses.

    It is not safe to use GioUnix (or GioUnix aliases in Gio) directly.
    Depends on the GLib/PyGObject combination the namespace can be either missing or broken.
    """

    DesktopAppInfo: type[Gio.DesktopAppInfo]
    InputStream: type[Gio.UnixInputStream]
    OutputStream: type[Gio.UnixOutputStream]


GioUnix = _GioUnixCompat()

with contextlib.suppress(ImportError, ValueError):
    gi.require_version("GioUnix", "2.0")
    from gi.repository import GioUnix as _SystemGioUnix  # type: ignore[no-redef, attr-defined]

    for attr_name in ("DesktopAppInfo", "InputStream", "OutputStream"):
        with contextlib.suppress(AttributeError):
            setattr(GioUnix, attr_name, getattr(_SystemGioUnix, attr_name))


def _ensure_attr(attr_name: str, gio_attr_name: str) -> None:
    if hasattr(GioUnix, attr_name):
        return

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        fallback = getattr(Gio, gio_attr_name, None)

    if fallback is None:
        err_msg = f"Neither GioUnix.{attr_name} nor Gio.{gio_attr_name} could be found"
        raise ImportError(err_msg)

    setattr(GioUnix, attr_name, fallback)


_ensure_attr("InputStream", "UnixInputStream")
_ensure_attr("OutputStream", "UnixOutputStream")
