# -*- Mode: Python; coding: utf-8;

import logging
from gi.repository import Gtk

logger = logging.getLogger(__name__)


class ResultItemWidget(Gtk.EventBox):
    __gtype_name__ = "ResultItemWidget"
    shortcut = None

    index = None
    builder = None
    name = None
    query = None
    item_object = None

    def initialize(self, builder, item_object, index, query):
        self.builder = builder
        item_frame = self.builder.get_object('item-frame')
        item_frame.connect("button-release-event", self.on_click)
        item_frame.connect("enter_notify_event", self.on_mouse_hover)

        self.item_object = item_object
        self.query = query
        self.set_index(index)

        self.set_icon(item_object.get_icon())
        self.set_name(item_object.get_name())
        self.set_description(item_object.get_description())

    def set_index(self, index):
        """
        Set index for the item and assign shortcut
        """
        self.index = index
        self.shortcut = 'Alt+%s' % (index + 1)
        self.set_shortcut(self.shortcut)

    def select(self):
        self.set_shortcut('⏎')
        self.get_style_context().add_class('selected')

    def deselect(self):
        self.set_shortcut(self.shortcut)
        self.get_style_context().remove_class('selected')

    def set_icon(self, icon):
        """
        Icon can be either a PixBuf instance or None (the default is used)
        """
        if icon:
            iconWgt = self.builder.get_object('item-icon')
            iconWgt.set_from_pixbuf(icon)

    def set_name(self, name):
        self.builder.get_object('item-name').set_text(name.replace('{query}', self.query or '...'))
        self.name = name

    def get_name(self):
        return self.name

    def on_click(self, widget, event):
        self.get_toplevel().select_result_item(self.index)
        self.get_toplevel().enter_result_item()

    def on_mouse_hover(self, widget, event):
        self.get_toplevel().select_result_item(self.index)

    def set_description(self, description):
        if description:
            self.builder.get_object('item-descr').set_text(description.replace('{query}', self.query or '...'))
        else:
            self.builder.get_object('item-descr').destroy()

    def set_shortcut(self, text):
        return self.builder.get_object('item-shortcut').set_text(text)

    def on_enter(self, argument=None):
        return self.item_object.on_enter(argument)

    def get_keyword(self):
        return self.item_object.get_keyword()
