from __future__ import annotations

from time import time
from typing import Any, Callable, TypeVar

from gi.repository import GLib, Gtk

T = TypeVar("T", bound=Gtk.Widget)

# Shared constants
ICON_SIZE_S = 24
ICON_SIZE_M = 32
ICON_SIZE_L = 48
ICON_SIZE_XL = 64
SIDEBAR_WIDTH = 280
SPINNER_MIN_ANIMATION_MS = 250


def styled(widget: T, *class_names: str) -> T:
    style = widget.get_style_context()
    for class_name in class_names:
        style.add_class(class_name)
    return widget


def start_spinner_button_animation(button: Gtk.Button) -> Callable[[], None]:
    """
    Starts the spinner animation for a button with a minimum animation duration
    Returns a function to stops the animation
    """
    start_time = time()
    btn_style = button.get_style_context()
    btn_style.add_class("spinner-button")
    button.set_sensitive(False)

    def do_stop_animation() -> None:
        btn_style.remove_class("spinner-button")
        button.set_sensitive(True)

    def stop_animation() -> None:
        time_passed = int((time() - start_time) * 1000)
        timeout = max(0, SPINNER_MIN_ANIMATION_MS - time_passed)
        GLib.timeout_add(timeout, do_stop_animation)

    return stop_animation


class BaseView(Gtk.Box):
    window: Gtk.Window
    """Base class for preference views (for public methods)"""

    def __init__(self, window: Gtk.Window, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.window = window

    def save_changes(self) -> bool:
        """Save changes and return True if successful, False otherwise.

        This is a no-op implementation that views can override to handle Ctrl+S.
        """
        return False


class DataListBoxRow(Gtk.ListBoxRow):
    """A ListBox row that can store an id reference"""

    def __init__(self, identifier: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.id = identifier


class TextArea(Gtk.TextView):
    """A wrapper around Gtk.TextView that makes it easier to get and set the buffer"""

    def set_text(self, text: str) -> None:
        self.get_buffer().set_text(text)

    def get_text(self) -> str:
        buffer = self.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
