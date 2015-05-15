# -*- Mode: Python; coding: utf-8;

import logging
from gi.repository import Gtk

logger = logging.getLogger(__name__)


class ResultItem(Gtk.EventBox):
    __gtype_name__ = "ResultItem"
    shortcut = None

    index = None
    builder = None
    name = None

    def set_index(self, index):
        """
        Set index for the item and assign shortcut
        """
        self.index = index
        self.shortcut = 'Alt+%s' % (index + 1)
        self.set_shortcut(self.shortcut)

    def set_builder(self, builder):
        """
        :param Gtk.Builder builder:
        """

        self.builder = builder

        item_frame = self.builder.get_object('item-frame')
        item_frame.connect("button-release-event", self.on_click)
        item_frame.connect("enter_notify_event", self.on_mouse_hover)

    def select(self):
        self.set_shortcut('⏎')
        self.get_style_context().add_class('selected')

    def deselect(self):
        self.set_shortcut(self.shortcut)
        self.get_style_context().remove_class('selected')

    def set_default_icon(self):
        """
        If we don't set any icon, it will be a default stock icon gtk-missing-image
        """
        pass

    def set_icon(self, icon):
        """
        Icon can be either a PixBuf instance or None (the default is used)
        """
        iconWgt = self.builder.get_object('item-icon')
        iconWgt.set_from_pixbuf(icon) if icon else self.set_default_icon()

    def set_name(self, name):
        self.builder.get_object('item-name').set_text(name)
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
            self.builder.get_object('item-descr').set_text(description)
        else:
            self.builder.get_object('item-descr').destroy()

    def set_shortcut(self, text):
        return self.builder.get_object('item-shortcut').set_text(text)

    def set_metadata(self, metadata):
        self.metadata = metadata

    def get_desktop_file_path(self):

        return self.metadata.get('desktop_file')

    def enter(self):
        """
        Should be implemented in derived classes
        Return True if launcher window needs to be hidden
        """
        pass
