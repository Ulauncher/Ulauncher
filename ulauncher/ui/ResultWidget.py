import logging
from typing import Any
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import Gtk, Gdk

from ulauncher.config import ITEM_SHORTCUT_KEYS
from ulauncher.utils.display import get_monitor_scale_factor
from ulauncher.utils.icon import load_icon
from ulauncher.utils.Theme import Theme
from ulauncher.modes.Query import Query

logger = logging.getLogger(__name__)


class ResultWidget(Gtk.EventBox):
    __gtype_name__ = "ResultWidget"

    shortcut = ''  # type: str
    index = 0  # type: int
    builder = None  # type: Any
    name = ''  # type: str
    query = Query('')  # type: Query
    result = None  # type: Any
    item_box = None  # type: Any

    def initialize(self, builder: Any, result: Any, index: int, query: Query) -> None:
        self.builder = builder
        item_frame = self.builder.get_object('item-frame')
        item_frame.connect("button-release-event", self.on_click)
        item_frame.connect("enter_notify_event", self.on_mouse_hover)

        self.item_box = builder.get_object('item-box')
        self.result = result
        self.query = query
        self.set_index(index)

        self.set_icon(load_icon(result.icon, result.get_icon_size()))
        self.set_description(result.get_description(query))
        self.set_name_highlighted()

    def set_index(self, index):
        """
        Set index for the item and assign shortcut
        """
        self.index = index
        self.shortcut = f"Alt+{ITEM_SHORTCUT_KEYS[index]}"
        self.set_shortcut(self.shortcut)

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
        if not icon:
            return

        iconWgt = self.builder.get_object('item-icon')
        scale_factor = get_monitor_scale_factor()

        if scale_factor == 1:
            iconWgt.set_from_pixbuf(icon)
            return

        surface = Gdk.cairo_surface_create_from_pixbuf(icon, scale_factor, self.get_window())
        iconWgt.set_from_surface(surface)

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
