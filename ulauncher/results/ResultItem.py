# -*- Mode: Python; coding: utf-8;

import logging
from gi.repository import Gtk, GdkPixbuf

logger = logging.getLogger(__name__)


class ResultItem(Gtk.EventBox):
    __gtype_name__ = "ResultItem"
    ICON_SIZE = 40
    shortcut = None

    index = None
    builder = None

    @classmethod
    def load_icon(cls, image_src):
        return GdkPixbuf.Pixbuf.new_from_file_at_size(image_src, cls.ICON_SIZE, cls.ICON_SIZE)

    def set_index(self, index):
        self.index = index
        self.shortcut = 'Alt+%s' % (index + 1)
        self.set_shortcut(self.shortcut)

    def set_builder(self, builder):

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
        Icon can be either a string - path to file
        or a PixBuf object
        """
        iconWgt = self.builder.get_object('item-icon')
        if isinstance(icon, str):
            try:
                iconWgt.set_from_pixbuf(self.load_icon(icon))
            except Exception as e:
                logger.debug('Failed to load icon from file %s -> %s', icon, e)
                self.set_default_icon()
        elif isinstance(icon, GdkPixbuf.Pixbuf):
            iconWgt.set_from_pixbuf(icon)
        else:
            self.set_default_icon()

    def set_name(self, name):

        self.builder.get_object('item-name').set_text(name)

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

    def run(self):
        """
        Should be implemented in derived classes
        Return True if launcher window needs to be hidden
        """
        pass
