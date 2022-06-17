import gi
gi.require_versions({"Gtk": "3.0", "WebKit2": "4.0"})
# pylint: disable=wrong-import-position,unused-argument
from gi.repository import Gtk, WebKit2
from ulauncher.config import get_asset, get_options
from ulauncher.ui.preferences_context_server import PreferencesContextServer


class PreferencesWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(
            title="Ulauncher Preferences",
            window_position=Gtk.WindowPosition.CENTER,
            **kwargs
        )

        self.set_default_size(1000, 600)
        self._init_webview()
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

        server = PreferencesContextServer.get_instance(self.get_application())
        self.webview = WebKit2.WebView(settings=settings, web_context=server.context)
        server.client = self.webview
        self.add(self.webview)
        self.webview.show()
        self.load_page()
        # Show right click menu if running with --dev flag
        self.webview.connect('context-menu', lambda *_: not get_options().dev)

        inspector = self.webview.get_inspector()
        inspector.connect("attach", lambda inspector, target_view: WebKit2.WebView())

    def load_page(self, page=''):
        self.webview.load_uri(f"file2://{get_asset('preferences', 'index.html')}#/{page}")

    def on_delete(self, *_):
        # Override default event when the user presses the close button in the menubar
        self.hide()
        return True

    # pylint: disable=arguments-differ
    def present(self, page):
        self.load_page(page)
        super().present()

    def show(self, page):
        self.load_page(page)
        super().show()
