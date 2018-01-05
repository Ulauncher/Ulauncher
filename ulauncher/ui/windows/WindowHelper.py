from gi.repository import Gtk


class WindowHelper(object):

    css_provider = None

    def init_styles(self, path):
        if not self.css_provider:
            self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_path(path)
        self.apply_css(self)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None and screen.is_composited():
            self.set_visual(visual)

    def apply_css(self, widget):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      self.css_provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css)
