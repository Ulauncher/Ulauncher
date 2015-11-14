from gi.repository import Gtk


class WindowHelper(object):

    provider = None

    def init_styles(self, path):
        self.provider = Gtk.CssProvider()
        self.provider.load_from_path(path)
        self.apply_css(self, self.provider)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None and screen.is_composited():
            self.set_visual(visual)

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)
