from __future__ import annotations

from typing import Any

from gi.repository import Gdk, Gtk

from ulauncher import paths
from ulauncher.ui.windows.preferences.views import BaseView, styled
from ulauncher.ui.windows.preferences.views.about import AboutView
from ulauncher.ui.windows.preferences.views.extensions import ExtensionsView
from ulauncher.ui.windows.preferences.views.help import HelpView
from ulauncher.ui.windows.preferences.views.preferences import PreferencesView
from ulauncher.ui.windows.preferences.views.shortcuts import ShortcutsView

VIEW_CONFIG: list[tuple[str, str, type[BaseView]]] = [
    ("Preferences", "preferences-system-symbolic", PreferencesView),
    ("Shortcuts", "go-next-symbolic", ShortcutsView),
    ("Extensions", "application-x-addon-symbolic", ExtensionsView),
    ("Help", "help-browser-symbolic", HelpView),
    ("About", "help-about-symbolic", AboutView),
]
WINDOW_DEFAULT_WIDTH = 1000
WINDOW_DEFAULT_HEIGHT = 600


class PreferencesWindow(Gtk.ApplicationWindow):
    """Main preferences window with tabbed interface"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            title="Ulauncher Preferences", window_position=Gtk.WindowPosition.CENTER, resizable=True, **kwargs
        )

        self.set_default_size(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)

        # Store views for keybinding access
        self.views: list[BaseView] = []

        # Create the main UI
        self._create_ui()

        # Setup keyboard shortcuts
        self._setup_keybindings()

    def _create_ui(self) -> None:
        """Create the main UI with notebook tabs"""
        # Create main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(main_box)

        # Create notebook for tabs
        self.notebook: Gtk.Notebook = Gtk.Notebook(tab_pos=Gtk.PositionType.TOP)
        main_box.pack_start(self.notebook, True, True, 0)

        # Store views in dictionary for easy access
        for name, icon_name, view_class in VIEW_CONFIG:
            view = view_class(self)
            self.views.append(view)
            self._add_view(view, icon_name, name)

        # Setup custom styling
        self._setup_custom_styling()

        main_box.show_all()

    def _add_view(self, view: Gtk.Widget, icon_name: str, label_text: str) -> None:
        tab_box = self._create_tab_header(icon_name, label_text)
        # Wrap page in background container
        view_bg = styled(Gtk.Box(), "view-container")
        view_bg.pack_start(view, True, True, 0)
        self.notebook.append_page(view_bg, tab_box)

    def _create_tab_header(self, icon_name: str, label_text: str) -> Gtk.Box:
        """Create a tab header with icon and label"""
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.SMALL_TOOLBAR)
        label = Gtk.Label.new(label_text)
        tab_box.pack_start(icon, False, False, 0)
        tab_box.pack_start(label, False, False, 0)
        tab_box.show_all()
        return tab_box

    def present(self, view: str | None = None) -> None:
        self.show(view)
        super().present()

    def show(self, view: str | None = None) -> None:
        if view:
            for index, (name, *_) in enumerate(VIEW_CONFIG):
                if view == name.lower():
                    self.notebook.set_current_page(index)
                    break
        super().show()

    def _setup_keybindings(self) -> None:
        """Setup keyboard shortcuts for the preferences window"""
        # Connect key press event
        self.connect("key-press-event", self._on_key_press)

    def _on_key_press(self, _widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        """Handle key press events for keyboard shortcuts"""
        current_page = self.notebook.get_current_page()
        # Ctrl+S
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and event.keyval == Gdk.KEY_s:
            return self.views[current_page].save_changes()
        return False

    def _setup_custom_styling(self) -> None:
        """Setup custom CSS styling for softer appearance"""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(f"{paths.ASSETS}/preferences.css")

        screen = Gdk.Screen.get_default()
        if screen:
            Gtk.StyleContext.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
