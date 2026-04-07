"""
Centralized GI module imports for Ulauncher.

This is the single canonical place to import all GI/GObject-Introspection modules.
gi.require_versions() is called here; ulauncher/__init__.py guarantees this module
loads before any other code imports from gi.repository.

Do NOT use `from gi.repository import ...` elsewhere; use `from ulauncher.gi import ...`.
"""

from __future__ import annotations

import contextlib
import types
import warnings

import gi  # absolute import — finds the real gi package, not this file

gi.require_versions(
    {
        "Gtk": "3.0",
        "Gdk": "3.0",
        "GdkX11": "3.0",
        "GdkPixbuf": "2.0",
        "Pango": "1.0",
    }
)

from gi.repository import (  # type: ignore[attr-defined]  # noqa: E402
    Gdk,
    GdkPixbuf,
    GdkX11,  # pyrefly: ignore[missing-module-attribute]
    Gio,
    GLib,
    GObject,
    Gtk,
    Pango,
)

__all__ = [
    "GLib",
    "GObject",
    "Gdk",
    "GdkPixbuf",
    "GdkX11",
    "Gio",
    "GioUnix",
    "Gtk",
    "Pango",
]

# ─── GioUnix compatibility namespace ──────────────────────────────────────────
#
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
# - GioUnix imports, but symbols are missing
# - GioUnix imports, but older GLib with PyGObject 3.54.x still gives unbound methods
# - PyGObject 3.55.0+ should be safe to use with all versions of GLib


class _GioUnixCompat(types.SimpleNamespace):
    """
    Lightweight namespace mimicking GioUnix for the symbols Ulauncher uses.

    It is not safe to use GioUnix (or GioUnix aliases in Gio) directly.
    Depending on the GLib/PyGObject combination the namespace can be either missing or broken.
    """

    DesktopAppInfo: type[DesktopAppInfo]  # forward ref; class is defined below and patched in
    InputStream: type[Gio.UnixInputStream]
    OutputStream: type[Gio.UnixOutputStream]


GioUnix = _GioUnixCompat()

with contextlib.suppress(ImportError, ValueError):
    gi.require_version("GioUnix", "2.0")
    from gi.repository import GioUnix as _SystemGioUnix  # type: ignore[no-redef, attr-defined]

    for _attr_name in ("DesktopAppInfo", "InputStream", "OutputStream"):
        with contextlib.suppress(AttributeError):
            setattr(GioUnix, _attr_name, getattr(_SystemGioUnix, _attr_name))


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
_ensure_attr("DesktopAppInfo", "DesktopAppInfo")

# ─── DesktopAppInfo wrapper ────────────────────────────────────────────────────
#
# GioUnix.DesktopAppInfo has unbound method bugs across certain GLib/PyGObject
# version combinations. We wrap it and patch it back onto GioUnix so all callers
# get the fixed version transparently via GioUnix.DesktopAppInfo.

_RawDesktopAppInfo = GioUnix.DesktopAppInfo  # the raw (potentially broken) class


class DesktopAppInfo:
    """Wrapper for GioUnix.DesktopAppInfo without the bork."""

    _app_info: _RawDesktopAppInfo  # type: ignore[valid-type]

    def __init__(self, app_info: _RawDesktopAppInfo) -> None:  # type: ignore[valid-type]
        self._app_info = app_info

    @staticmethod
    def new(app_id: str) -> DesktopAppInfo | None:
        if app_info := _RawDesktopAppInfo.new(app_id):
            return DesktopAppInfo(app_info)
        return None

    @staticmethod
    def new_from_filename(filename: str) -> DesktopAppInfo | None:
        if app_info := _RawDesktopAppInfo.new_from_filename(filename):
            return DesktopAppInfo(app_info)
        return None

    @staticmethod
    def get_all() -> list[DesktopAppInfo]:
        return [DesktopAppInfo(app_info) for app_info in _RawDesktopAppInfo.get_all()]  # type: ignore[arg-type]

    # Methods copied from GioUnix.DesktopAppInfo (these work fine)

    def get_id(self) -> str | None:
        return self._app_info.get_id()

    def get_name(self) -> str:
        return self._app_info.get_name()

    def get_description(self) -> str | None:
        return self._app_info.get_description()

    def get_display_name(self) -> str:
        return self._app_info.get_display_name()

    def get_commandline(self) -> str | None:
        return self._app_info.get_commandline()

    def get_executable(self) -> str:
        return self._app_info.get_executable()

    def get_icon(self) -> Gio.Icon | None:
        return self._app_info.get_icon()

    # Borked unbound methods that we have to call via the class to work consistently
    def get_boolean(self, name: str) -> bool:
        return _RawDesktopAppInfo.get_boolean(self._app_info, name)

    def get_string(self, name: str) -> str | None:
        return _RawDesktopAppInfo.get_string(self._app_info, name)

    def get_generic_name(self) -> str | None:
        return _RawDesktopAppInfo.get_generic_name(self._app_info)

    def get_filename(self) -> str | None:
        return _RawDesktopAppInfo.get_filename(self._app_info)

    def get_keywords(self) -> list[str]:
        return _RawDesktopAppInfo.get_keywords(self._app_info)

    def get_show_in(self) -> bool:
        return _RawDesktopAppInfo.get_show_in(self._app_info)

    def get_nodisplay(self) -> bool:
        return _RawDesktopAppInfo.get_nodisplay(self._app_info)


GioUnix.DesktopAppInfo = DesktopAppInfo  # type: ignore[assignment]
