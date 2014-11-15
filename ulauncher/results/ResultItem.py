from gi.repository import Gtk, GdkPixbuf


class ResultItem(Gtk.Frame):
    __gtype_name__ = "ResultItem"
    ICON_SIZE = 40

    @classmethod
    def load_icon(cls, image_src):
        return GdkPixbuf.Pixbuf.new_from_file_at_size(image_src, cls.ICON_SIZE, cls.ICON_SIZE)

    def set_builder(self, builder):
        self.builder = builder

    def select(self):
        return self.get_style_context().add_class('selected')

    def deselect(self):
        return self.get_style_context().remove_class('selected')

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
                iconWgt.set_from_pixbuf(load_icon(icon))
            except:
                self.set_default_icon()
        elif isinstance(icon, GdkPixbuf.Pixbuf):
            iconWgt.set_from_pixbuf(icon)
        else:
            self.set_default_icon()

    def set_name(self, name):
        self.builder.get_object('item-name').set_text(name)

    def set_description(self, description):
        if description:
            self.builder.get_object('item-descr').set_text(description)
        else:
            self.builder.get_object('item-descr').destroy()

    def set_shortcut(self, shortcut_num):
        self.builder.get_object('item-shortcut').set_text('Alt+' + str(shortcut_num))

    def set_metadata(self, metadata):
        self.metadata = metadata

    def run(self):
        """
        Should be implemented in derived classes
        Return True if launcher window needs to be hidden
        """
        pass
