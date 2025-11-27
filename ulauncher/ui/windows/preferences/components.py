"""Common UI components for preferences views"""

from __future__ import annotations

from gi.repository import Gtk

from ulauncher.ui.windows.preferences.views import styled


def create_warning_box(
    message: str, use_markup: bool = False, selectable: bool = False, max_width_chars: int = 80
) -> Gtk.Box:
    """Create a styled warning/info box with message text.

    This creates a box with the 'ext-error-frame' styling (amber/yellow background)
    suitable for displaying warnings, notes, or informational messages.

    Args:
        message: The warning or info text to display
        use_markup: If True, interpret the message as Pango markup
        selectable: If True, allow the user to select and copy the text
        max_width_chars: Maximum width in characters before wrapping

    Returns:
        A styled Gtk.Box containing the message label

    Example:
        >>> warning = create_warning_box(
        ...     "Ulauncher doesn't support setting global shortcuts for your desktop environment.\\n"
        ...     "Bind this command in your DE settings: gapplication launch io.ulauncher.Ulauncher"
        ... )
        >>> parent_container.pack_start(warning, False, False, 0)
    """
    warning_frame = styled(Gtk.Box(spacing=0), "ext-error-frame")

    label = Gtk.Label(
        label=message,
        use_markup=use_markup,
        halign=Gtk.Align.START,
        wrap=True,
        selectable=selectable,
        max_width_chars=max_width_chars,
    )
    label.set_xalign(0.0)

    warning_frame.pack_start(label, False, False, 0)
    return warning_frame
