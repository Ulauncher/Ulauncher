"""Launch contexts that let launched apps take focus.

GTK asks the compositor for an xdg-activation token tied to the last input on the focused
surface, so a startup ID must be requested before Ulauncher's window hides. Under XWayland
it is an X11 startup ID, which Mutter also accepts as an activation token.
"""

from __future__ import annotations

from ulauncher.gi import Gio


class _ActivationPending:
    value = False


def get_launch_context() -> Gio.AppLaunchContext:
    from gi.repository import Gdk  # noqa: TID251 - only called from the UI process, where GTK is loaded

    display = Gdk.Display.get_default()
    if not display:
        return Gio.AppLaunchContext()
    _ActivationPending.value = True
    return display.get_app_launch_context()


def take_activation_pending() -> bool:
    """Whether a launch context was handed out since the last call."""
    pending = _ActivationPending.value
    _ActivationPending.value = False
    return pending
