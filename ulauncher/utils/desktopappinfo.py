from gi.repository import Gio

try:
    DesktopAppInfo = Gio.DesktopAppInfo
except AttributeError:
    import gi

    try:
        gi.require_version("GioUnix", "2.0")
        from gi.repository import GioUnix  # type: ignore[attr-defined]

        DesktopAppInfo = GioUnix.DesktopAppInfo  # type: ignore[assignment,misc,unused-ignore]
    except (ImportError, ValueError, AttributeError):
        raise ImportError("Could not import Gio.DesktopAppInfo")
