from __future__ import annotations

import logging
from html import unescape

from gi.repository import Gdk, Gtk, Pango

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.utils.load_icon_surface import load_icon_surface
from ulauncher.utils.settings import Settings
from ulauncher.utils.text_highlighter import highlight_text
from ulauncher.utils.wm import get_text_scaling_factor

ELLIPSIZE_MIN_LENGTH = 6
ELLIPSIZE_FORCE_AT_LENGTH = 20
logger = logging.getLogger()


class ResultWidget(Gtk.EventBox):
    index: int = 0
    name: str
    query: Query
    result: Result
    item_box: Gtk.EventBox
    shortcut_label: Gtk.Label
    title_box: Gtk.Box
    text_container: Gtk.Box

    def __init__(self, result: Result, index: int, query: Query) -> None:
        self.result = result
        self.query = query
        text_scaling_factor = get_text_scaling_factor()
        icon_size = 25 if result.compact else 40
        inner_margin_x = int(12.0 * text_scaling_factor)
        outer_margin_x = int(18.0 * text_scaling_factor)
        margin_y = (3 if result.compact else 5) * text_scaling_factor

        super().__init__()
        self.get_style_context().add_class("item-frame")
        self.connect("button-release-event", self.on_click)
        self.connect("enter_notify_event", self.on_mouse_hover)

        self.item_box = Gtk.EventBox()
        self.item_box.get_style_context().add_class("item-box")
        self.add(self.item_box)
        item_container = Gtk.Box()
        item_container.get_style_context().add_class("item-container")
        self.item_box.add(item_container)

        icon = Gtk.Image()
        icon.set_from_surface(load_icon_surface(result.icon or "gtk-missing-image", icon_size, self.get_scale_factor()))
        icon.get_style_context().add_class("item-icon")
        item_container.pack_start(icon, False, True, 0)

        self.text_container = Gtk.Box(
            width_request=int(350.0 * text_scaling_factor),
            margin_start=inner_margin_x,
            margin_end=inner_margin_x,
            orientation=Gtk.Orientation.VERTICAL,
        )
        item_container.pack_start(self.text_container, True, True, 0)

        self.shortcut_label = Gtk.Label(justify=Gtk.Justification.RIGHT, width_request=44)
        self.shortcut_label.get_style_context().add_class("item-shortcut")
        self.shortcut_label.get_style_context().add_class("item-text")
        item_container.pack_end(self.shortcut_label, False, True, 0)

        self.set_index(index)

        item_container.get_style_context().add_class("small-result-item")

        self.title_box = Gtk.Box()
        self.title_box.get_style_context().add_class("item-name")
        self.title_box.get_style_context().add_class("item-text")

        # title_box should fill vertical space if there's no description
        should_expand = not result.compact and not result.description

        self.text_container.pack_start(self.title_box, should_expand, True, 0)

        item_container.set_property("margin-start", outer_margin_x)
        item_container.set_property("margin-end", outer_margin_x)
        item_container.set_property("margin-top", margin_y)
        item_container.set_property("margin-bottom", margin_y)

        if result.description and not result.compact:
            descr_label = Gtk.Label(hexpand=True, max_width_chars=1, xalign=0, ellipsize=Pango.EllipsizeMode.MIDDLE)
            descr_label.get_style_context().add_class("item-descr")
            descr_label.get_style_context().add_class("item-text")
            descr_label.set_text(unescape(result.description))
            self.text_container.pack_start(descr_label, False, True, 0)
        self.highlight_name()

    def set_index(self, index: int) -> None:
        """
        Set index for the item and assign shortcut
        """
        jump_keys = Settings.load().get_jump_keys()
        if index < len(jump_keys):
            self.index = index
            self.shortcut_label.set_text(f"Alt+{jump_keys[index]}")

    def select(self) -> None:
        self.item_box.get_style_context().add_class("selected")
        self.scroll_to_focus()

    def deselect(self) -> None:
        self.item_box.get_style_context().remove_class("selected")

    def scroll_to_focus(self) -> None:
        viewport: Gtk.Viewport = self.get_ancestor(Gtk.Viewport)  # type: ignore[assignment]
        viewport_height = viewport.get_allocation().height
        scroll_y = viewport.get_vadjustment().get_value()
        allocation = self.get_allocation()
        bottom = allocation.y + allocation.height
        if scroll_y > allocation.y:  # Scroll up if the widget is above visible area
            viewport.set_vadjustment(Gtk.Adjustment(allocation.y, 0, 2**32, 1, 10, 0))
        elif viewport_height + scroll_y < bottom:  # Scroll down if the widget is below visible area
            viewport.set_vadjustment(Gtk.Adjustment(bottom - viewport_height, 0, 2**32, 1, 10, 0))

    def highlight_name(self) -> None:
        highlightable_input = self.result.get_highlightable_input(self.query)
        if highlightable_input and (self.result.searchable or self.result.highlightable):
            labels = []

            for label_text, is_highlight in highlight_text(highlightable_input, self.result.name):
                ellipsize_min = (not is_highlight and ELLIPSIZE_MIN_LENGTH) or ELLIPSIZE_FORCE_AT_LENGTH
                ellipsize = Pango.EllipsizeMode.MIDDLE if len(label_text) > ellipsize_min else Pango.EllipsizeMode.NONE
                label = Gtk.Label(label=unescape(label_text), ellipsize=ellipsize)
                if is_highlight:
                    label.get_style_context().add_class("item-highlight")
                labels.append(label)
        else:
            labels = [Gtk.Label(label=self.result.name, ellipsize=Pango.EllipsizeMode.MIDDLE)]

        for label in labels:
            self.title_box.pack_start(label, False, False, 0)

    def on_click(self, _widget: Gtk.Widget, event: Gdk.EventButton | None = None) -> None:
        window = self.get_toplevel()
        window.select_result(self.index)  # type: ignore[attr-defined]
        alt = bool(event and event.button != 1)  # right click
        window.results_nav.activate(alt)  # type: ignore[attr-defined]

    def on_mouse_hover(self, _widget: Gtk.Widget, event: Gdk.EventCrossing) -> None:
        # event.time is 0 it means the mouse didn't move, but the window scrolled behind the mouse
        if event.time:
            self.get_toplevel().select_result(self.index)  # type: ignore[attr-defined]
