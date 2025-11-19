from __future__ import annotations

import logging
from typing import Any

from gi.repository import Gdk, Gio, GLib, Gtk

from ulauncher import paths
from ulauncher.ui.windows.preferences.views import BaseView, styled
from ulauncher.ui.windows.preferences.views.about import AboutView
from ulauncher.ui.windows.preferences.views.extensions import ExtensionsView
from ulauncher.ui.windows.preferences.views.help import HelpView
from ulauncher.ui.windows.preferences.views.preferences import PreferencesView
from ulauncher.ui.windows.preferences.views.shortcuts import ShortcutsView

VIEW_CONFIG: list[tuple[str, type[BaseView]]] = [
    ("Preferences", PreferencesView),
    ("Shortcuts", ShortcutsView),
    ("Extensions", ExtensionsView),
    ("Help", HelpView),
    ("About", AboutView),
]
WINDOW_DEFAULT_WIDTH = 1000
WINDOW_DEFAULT_HEIGHT = 600

logger = logging.getLogger(__name__)


class PreferencesWindow(Gtk.ApplicationWindow):
    """Main preferences window with tabbed interface"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            title="Ulauncher Preferences", window_position=Gtk.WindowPosition.CENTER, resizable=True, **kwargs
        )

        self.set_default_size(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)

        # Store views keyed by stack page name for keybinding access
        self.views: dict[str, BaseView] = {}
        self._css_provider: Gtk.CssProvider | None = None
        self._css_monitor: Gio.FileMonitor | None = None

        # Create the main UI
        self._create_ui()

        # Setup keyboard shortcuts
        self._setup_keybindings()

        # Setup CSS file monitoring
        self._setup_css_monitoring()

    def _create_ui(self) -> None:
        """Create the main UI with notebook tabs"""
        # Create main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(main_box)

        # Create stack for view navigation
        self.stack: Gtk.Stack = Gtk.Stack(
            transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT, transition_duration=200
        )
        main_box.pack_start(self.stack, True, True, 0)

        # Place navigation in the header bar
        self._create_headerbar()

        for name, view_class in VIEW_CONFIG:
            view = view_class(self)
            self._add_view(view, name)

        # Setup custom styling
        self._setup_custom_styling()

        main_box.show_all()

    def _create_headerbar(self) -> None:
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.get_style_context().add_class("preferences-header")

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(self.stack)
        stack_switcher.set_halign(Gtk.Align.CENTER)
        stack_switcher.set_hexpand(False)
        stack_switcher.get_style_context().add_class("preferences-nav")

        header_bar.set_custom_title(stack_switcher)
        self.set_titlebar(header_bar)
        header_bar.show_all()

    def _add_view(self, view: BaseView, label_text: str) -> None:
        # Wrap page in background container
        view_bg = styled(Gtk.Box(), "view-container")
        view_bg.pack_start(view, True, True, 0)
        page_name = label_text.lower()
        self.stack.add_titled(view_bg, page_name, label_text)
        self.views[page_name] = view

    def present(self, view: str | None = None) -> None:
        self.show(view)
        super().present()

    def show(self, view: str | None = None) -> None:
        if view:
            page_name = view.lower()
            if self.stack.get_child_by_name(page_name):
                self.stack.set_visible_child_name(page_name)
        super().show()

    def _setup_keybindings(self) -> None:
        """Setup keyboard shortcuts for the preferences window"""
        # Connect key press event
        self.connect("key-press-event", self._on_key_press)

    def _on_key_press(self, _widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        """Handle key press events for keyboard shortcuts"""
        # Ctrl+S
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and event.keyval == Gdk.KEY_s:
            page_name = self.stack.get_visible_child_name()
            if page_name:
                return self.views[page_name].save_changes()
        return False

    def _setup_custom_styling(self) -> None:
        """Setup custom CSS styling for softer appearance"""
        self._css_provider = Gtk.CssProvider()
        self._load_preferences_css()
        screen = Gdk.Screen.get_default()
        if screen:
            Gtk.StyleContext.add_provider_for_screen(
                screen, self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def reload_styles(self) -> None:
        """Reload the CSS provider contents from disk."""
        self._load_preferences_css()

    def _load_preferences_css(self) -> None:
        if not self._css_provider:
            return
        css_path = f"{paths.ASSETS}/preferences.css"
        try:
            self._css_provider.load_from_path(css_path)
        except GLib.Error:
            logger.exception("Failed to load preferences CSS from %s", css_path)

    def _setup_css_monitoring(self) -> None:
        """Setup file monitoring for CSS changes and auto-reload."""
        css_path = f"{paths.ASSETS}/preferences.css"
        css_file = Gio.File.new_for_path(css_path)

        try:
            self._css_monitor = css_file.monitor_file(Gio.FileMonitorFlags.NONE, None)
            self._css_monitor.connect("changed", self._on_css_file_changed)
            logger.info("Watching for CSS changes at %s", css_path)
        except GLib.Error:
            logger.exception("Failed to setup CSS file monitor for %s", css_path)

    def _on_css_file_changed(
        self,
        _monitor: Gio.FileMonitor,
        _file: Gio.File,
        _other_file: Gio.File | None,
        event_type: Gio.FileMonitorEvent,
    ) -> None:
        """Handle CSS file changes by reloading styles."""
        if event_type in (Gio.FileMonitorEvent.CHANGED, Gio.FileMonitorEvent.CREATED):
            logger.info("CSS file changed, reloading styles")
            self.reload_styles()
