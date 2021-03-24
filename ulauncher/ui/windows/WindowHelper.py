import gi
gi.require_version('Gtk', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import Gtk


class WindowHelper:

    css_provider = None

    def init_styles(self, path):
        if not self.css_provider:
            self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_path(path)
        self.apply_css(self)
        # pylint: disable=no-member
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)

    def apply_css(self, widget):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      self.css_provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css)
