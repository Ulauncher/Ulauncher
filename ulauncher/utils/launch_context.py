"""Launch contexts that let launched apps take focus.

GTK asks the compositor for an xdg-activation token tied to the last input on the focused
surface, so a startup ID must be requested before Ulauncher's window hides. Under XWayland
it is an X11 startup ID, which Mutter also accepts as an activation token.
"""

from __future__ import annotations

from ulauncher.gi import Gio


def get_launch_context() -> Gio.AppLaunchContext:
    from gi.repository import Gdk  # noqa: TID251 - only called from the UI process, where GTK is loaded

    display = Gdk.Display.get_default()
    return display.get_app_launch_context() if display else Gio.AppLaunchContext()
