import gi
gi.require_version('Gtk', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import Gtk


class WindowHelper:

    css_provider = None
    drag_start_coords = None

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

    ##############################################################
    # GTK mouse event handlers (attach to signals)               #
    # self.connect('button-press-event', self.mouse_down_event)  #
    # self.connect('button-release-event', self.mouse_up_event)  #
    # self.connect('motion_notify_event', self.mouse_move_event) #
    ##############################################################

    def mouse_down_event(self, _, event):
        """
        Prepare moving the window if the user drags
        """
        # Only on left click
        if event.button == 1:
            self.drag_start_coords = {'x': event.x, 'y': event.y}

    def mouse_up_event(self, *_):
        """
        Clear drag to move event data
        """
        self.drag_start_coords = None

    def mouse_move_event(self, _, event):
        """
        Move window if cursor is held
        """
        start = self.drag_start_coords
        if start:
            self.move(
                event.x_root - start['x'],
                event.y_root - start['y']
            )