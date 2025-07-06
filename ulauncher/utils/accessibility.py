from __future__ import annotations

import logging
from typing import Optional

from gi.repository import Atk, Gtk

logger = logging.getLogger()


def set_accessible_props(
    widget: Gtk.Widget,
    role: Optional[Atk.Role] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    label_for: Optional[Gtk.Widget] = None,
) -> None:
    """
    Set accessibility properties for a GTK widget.

    Args:
        widget: The GTK widget to set properties for
        role: The accessibility role (from Atk.Role)
        name: The accessible name
        description: The accessible description
        label_for: Widget that this widget is a label for
    """
    try:
        accessible = widget.get_accessible()

        if role is not None:
            accessible.set_role(role)

        if name is not None:
            accessible.set_name(name)

        if description is not None:
            accessible.set_description(description)

        if label_for is not None:
            label_widget = label_for.get_accessible()
            if label_widget:
                accessible.add_relationship(Atk.RelationType.LABEL_FOR, label_widget)

    except Exception as e:
        logger.warning(f"Failed to set accessibility properties: {e}")


def announce_for_screen_reader(widget: Gtk.Widget, text: str) -> None:
    """
    Announce text for screen readers.

    Args:
        widget: The widget to announce from
        text: The text to announce
    """
    try:
        accessible = widget.get_accessible()
        if hasattr(accessible, "notify_state_change"):
            # First set the description
            accessible.set_description(text)

            # Then notify of a state change to trigger screen reader announcement
            accessible.notify_state_change(Atk.StateType.SHOWING, True)
    except Exception as e:
        logger.warning(f"Failed to announce for screen reader: {e}")


def make_focusable(widget: Gtk.Widget) -> None:
    """
    Make a widget focusable and accessible via keyboard.

    Args:
        widget: The widget to make focusable
    """
    widget.set_can_focus(True)

    # Ensure the widget can receive keyboard events
    if isinstance(widget, Gtk.Button) or isinstance(widget, Gtk.Entry):
        widget.set_receives_default(True)
