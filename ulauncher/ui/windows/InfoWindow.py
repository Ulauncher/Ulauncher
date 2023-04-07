import logging
from gi.repository import Gtk, Gdk, WebKit2  # type: ignore[attr-defined]

class InfoWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_decorated(False)
        self.set_deletable(False)
        self.set_can_focus(False)
        self.set_skip_taskbar_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_keep_above(True)

        self.webview = WebKit2.WebView()
        self.webview.set_size_request(500, 500)
        self.webview.show()
        self.webview.load_html("", "file:///")
        self.add(self.webview)

        self.show_all()
        self.hide()

    def set_info(self, info: str):
        if info:
            if not self.visible:
                self.show_all()
            self.webview.load_html(info, "file:///")
        else:
            self.hide()

    @property
    def visible(self):
        return self.get_property("visible")
