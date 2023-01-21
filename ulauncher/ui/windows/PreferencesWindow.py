import os
from gi.repository import Gtk
from ulauncher.config import PATHS, get_options
from ulauncher.utils.WebKit2 import WebKit2
from ulauncher.ui.preferences_server import PreferencesServer


class PreferencesWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(title="Ulauncher Preferences", window_position="center", **kwargs)

        self.set_default_size(1000, 600)
        self._init_webview()
        # Kill the child WebKitNetworkProcess when the window is closed (there's no clean way to do this)
        self.connect("delete-event", self.on_delete)

    def _init_webview(self):
        settings = WebKit2.Settings(
            enable_developer_extras=bool(get_options().dev),
            enable_hyperlink_auditing=False,
            enable_page_cache=False,
            enable_write_console_messages_to_stdout=True,
            enable_xss_auditor=False,
            hardware_acceleration_policy=WebKit2.HardwareAccelerationPolicy.NEVER,
        )

        server = PreferencesServer.get_instance()
        self.webview = WebKit2.WebView(settings=settings, web_context=server.context)
        server.client = self.webview
        self.add(self.webview)
        self.webview.show()
        self.load_page()
        # Show right click menu if running with --dev flag
        self.webview.connect("context-menu", lambda *_: not get_options().dev)

    def load_page(self, page=""):
        self.webview.load_uri(f"prefs://{PATHS.ASSETS}/preferences/index.html#/{page}")

    # pylint: disable=arguments-differ
    def present(self, page=None):
        if page:
            self.load_page(page)
        super().present()

    def show(self, page=None):
        if page:
            self.load_page(page)
        super().show()

    def on_delete(self, *args, **kwargs):
        del self.get_application().preferences
        self.destroy()
        os.system(f"pkill -f WebKitNetworkProcess -P {os.getpid()}")
