import logging
from typing import Any
import gi
gi.require_version('Gtk', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import Gtk

from ulauncher.utils.Settings import Settings
from ulauncher.utils.display import get_scaling_factor
from ulauncher.utils.icon import load_icon
from ulauncher.utils.Theme import Theme
from ulauncher.modes.Query import Query

logger = logging.getLogger(__name__)


class ResultWidget(Gtk.EventBox):
    __gtype_name__ = "ResultWidget"

    index = 0  # type: int
    builder = None  # type: Any
    name = ''  # type: str
    query = Query('')  # type: Query
    result = None  # type: Any
    item_box = None  # type: Any
    scaling_factor = 1.0  # type: float

    def initialize(self, builder: Any, result: Any, index: int, query: Query) -> None:
        self.builder = builder
        item_frame = self.builder.get_object('item-frame')
        item_frame.connect("button-release-event", self.on_click)
        item_frame.connect("enter_notify_event", self.on_mouse_hover)

        self.item_box = builder.get_object('item-box')
        self.result = result
        self.query = query
        self.set_index(index)
        self.scaling_factor = get_scaling_factor()

        item_container = builder.get_object('item-container')
        item_name = builder.get_object('name_wrapper')
        base_scaling = 1.0

        if not item_name:
            item_name = builder.get_object('item-name')
            base_scaling = 0.67
        item_container.set_property('margin-start', 18 * self.scaling_factor)
        item_container.set_property('margin-end', 18 * self.scaling_factor)
        item_container.set_property('margin-top', 5 * base_scaling * self.scaling_factor)
        item_container.set_property('margin-bottom', 5 * base_scaling * self.scaling_factor)
        item_name.set_property('margin-start', 12 * base_scaling * self.scaling_factor)
        item_name.set_property('margin-end', 12 * base_scaling * self.scaling_factor)
        item_name.set_property('width-request', 350 * self.scaling_factor)

        self.set_icon(load_icon(result.icon, result.ICON_SIZE * self.scaling_factor))
        self.set_description(result.get_description(query))
        self.set_name_highlighted()

    def set_index(self, index):
        """
        Set index for the item and assign shortcut
        """
        jump_keys = Settings.get_instance().get_jump_keys()
        if index < len(jump_keys):
            self.index = index
            self.set_shortcut(f"Alt+{jump_keys[index]}")

    def select(self):
        self.set_name_highlighted(True)
        self.item_box.get_style_context().add_class('selected')

    def deselect(self):
        self.set_name_highlighted(False)
        self.item_box.get_style_context().remove_class('selected')

    def set_icon(self, icon):
        """
        :param PixBuf icon:
        """
        if icon:
            self.builder.get_object('item-icon').set_from_pixbuf(icon)

    def set_name_highlighted(self, is_selected: bool = False) -> None:
        colors = Theme.get_current().get_matched_text_hl_colors()
        color = colors['when_selected'] if is_selected else colors['when_not_selected']
        self.set_name(self.result.get_name_highlighted(self.query, color) or self.result.get_name())

    # pylint: disable=arguments-differ
    def set_name(self, name: str) -> None:
        item = self.builder.get_object('item-name')
        if '<span' in name:  # dealing with markup
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
        self.get_toplevel().select_result(self.index, onHover=True)

    def set_description(self, description):
        description_obj = self.builder.get_object('item-descr')
        if not description_obj:
            return

        if description:
            description_obj.set_text(description)
        else:
            description_obj.destroy()  # remove description label
            self.builder.get_object('item-name').set_margin_top(8)  # shift name label down to the center

    def set_shortcut(self, text):
        self.builder.get_object('item-shortcut').set_text(text)

    def get_keyword(self):
        return self.result.keyword
