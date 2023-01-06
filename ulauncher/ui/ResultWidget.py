import logging
from types import SimpleNamespace
from typing import Any
from gi.repository import Gtk
from ulauncher.utils.Settings import Settings
from ulauncher.utils.wm import get_text_scaling_factor
from ulauncher.utils.icon import load_icon_surface
from ulauncher.utils.text_highlighter import highlight_text
from ulauncher.utils.Theme import Theme
from ulauncher.api.shared.query import Query

logger = logging.getLogger()


class ResultWidget(Gtk.EventBox):  # type: ignore[name-defined]
    __gtype_name__ = "ResultWidget"

    index: int = 0
    builder: Any
    name: str
    query: Query
    result: Any
    item_box: Any
    compact = False

    def initialize(self, builder: Any, result: Any, index: int, query: Query) -> None:
        self.builder = builder
        item_frame = self.builder.get_object("item-frame")
        item_frame.connect("button-release-event", self.on_click)
        item_frame.connect("enter_notify_event", self.on_mouse_hover)

        self.item_box = builder.get_object("item-box")
        self.result = result
        self.compact = result.compact
        self.query = query
        self.set_index(index)
        text_scaling_factor = get_text_scaling_factor()

        item_container = builder.get_object("item-container")
        item_container.get_style_context().add_class("small-result-item")
        item_name = builder.get_object("name_wrapper")

        sizes = SimpleNamespace(
            icon=40,
            inner_margin_x=12 * text_scaling_factor,
            outer_margin_x=18 * text_scaling_factor,
            margin_y=5 * text_scaling_factor,
        )

        if self.compact:
            sizes.icon = 25
            sizes.margin_y = 3 * text_scaling_factor

        item_container.set_property("margin-start", sizes.outer_margin_x)
        item_container.set_property("margin-end", sizes.outer_margin_x)
        item_container.set_property("margin-top", sizes.margin_y)
        item_container.set_property("margin-bottom", sizes.margin_y)
        item_name.set_property("margin-start", sizes.inner_margin_x)
        item_name.set_property("margin-end", sizes.inner_margin_x)
        item_name.set_property("width-request", 350 * text_scaling_factor)

        self.set_icon(load_icon_surface(result.icon, sizes.icon, self.get_scale_factor()))
        self.set_description(result.get_description(query))  # need to run even if there is no descr
        self.set_name_highlighted()

    def set_index(self, index: int):
        """
        Set index for the item and assign shortcut
        """
        jump_keys = Settings.load().get_jump_keys()
        if index < len(jump_keys):
            self.index = index
            self.set_shortcut(f"Alt+{jump_keys[index]}")

    def select(self):
        self.set_name_highlighted(True)
        self.item_box.get_style_context().add_class("selected")
        self.scroll_to_focus()

    def deselect(self):
        self.set_name_highlighted(False)
        self.item_box.get_style_context().remove_class("selected")

    def scroll_to_focus(self):
        viewport = self.item_box.get_ancestor(Gtk.Viewport)
        viewport_height = viewport.get_allocation().height
        scroll_y = viewport.get_vadjustment().get_value()
        allocation = self.get_allocation()
        bottom = allocation.y + allocation.height
        if scroll_y > allocation.y:  # Scroll up if the widget is above visible area
            viewport.set_vadjustment(Gtk.Adjustment(allocation.y, 0, 2**32, 1, 10, 0))
        elif viewport_height + scroll_y < bottom:  # Scroll down if the widget is below visible area
            viewport.set_vadjustment(Gtk.Adjustment(bottom - viewport_height, 0, 2**32, 1, 10, 0))

    def set_icon(self, icon):
        """
        :param PixBuf icon:
        """
        if icon:
            self.builder.get_object("item-icon").set_from_surface(icon)

    def set_name_highlighted(self, is_selected=False):
        name = self.result.name
        colors = Theme.load(Settings.load().theme_name).matched_text_hl_colors
        color = colors.get("when_selected" if is_selected else "when_not_selected")
        highlightable_input = self.result.get_highlightable_input(self.query)
        if highlightable_input and (self.result.searchable or self.result.highlightable):
            name = highlight_text(
                highlightable_input, self.result.name, open_tag=f'<span foreground="{color}">', close_tag="</span>"
            )

        self.set_name(name)

    # pylint: disable=arguments-differ
    def set_name(self, name: str) -> None:
        item = self.builder.get_object("item-name")
        if "<span" in name:  # dealing with markup
            item.set_markup(name)
        else:
            item.set_text(name)
        self.name = name

    def get_name(self):
        return self.name

    # pylint: disable=unused-argument
    def on_click(self, widget, event=None):
        self.get_toplevel().select_result(self.index)
        alt_enter = bool(event and event.button != 1)
        self.get_toplevel().enter_result(alt=alt_enter)

    def on_mouse_hover(self, widget, event):
        # event.time is 0 it means the mouse didn't move, but the window scrolled behind the mouse
        if event.time:
            self.get_toplevel().select_result(self.index)

    def set_description(self, description):
        description_obj = self.builder.get_object("item-descr")

        if description and not self.compact:
            description_obj.set_text(description)
        else:
            description_obj.destroy()  # remove description label

    def set_shortcut(self, text):
        self.builder.get_object("item-shortcut").set_text(text)

    def get_keyword(self):
        return self.result.keyword
