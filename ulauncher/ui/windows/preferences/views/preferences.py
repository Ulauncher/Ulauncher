from __future__ import annotations

import logging
from typing import Any

from gi.repository import Gtk

from ulauncher.ui.windows.preferences.views import BaseView, styled
from ulauncher.utils.environment import IS_X11
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.hotkey_controller import HotkeyController
from ulauncher.utils.settings import Settings
from ulauncher.utils.systemd_controller import SystemdController
from ulauncher.utils.theme import get_themes

logger = logging.getLogger()
events = EventBus()


class PreferencesView(BaseView):
    """General preferences page"""

    def __init__(self, window: Gtk.Window) -> None:
        super().__init__(window, orientation=Gtk.Orientation.VERTICAL)
        self.settings: Settings = Settings.load()
        self.autostart_pref: SystemdController = SystemdController("ulauncher")

        scrolled = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.pack_start(scrolled, True, True, 0)

        # Create main container
        prefs_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=20, spacing=10)
        scrolled.add(prefs_view)

        # Add sections
        self._add_general_section(prefs_view)
        self._add_applications_section(prefs_view)
        self._add_advanced_section(prefs_view)

    def _add_section_header(self, parent: Gtk.Box, title: str) -> None:
        """Add a section header"""
        label = styled(
            Gtk.Label(
                label=title,
                halign=Gtk.Align.START,
                margin_top=20,
                margin_bottom=10,
            ),
            "title-3",
            "dim-label",
        )
        parent.pack_start(label, False, False, 0)

    def _add_setting_row(self, parent: Gtk.Box, label_text: str, widget: Gtk.Widget, description: str = "") -> None:
        """Add a settings row with label and widget"""
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin_bottom=15)

        # Left side - label and description
        label_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, width_request=380)

        label = Gtk.Label(label=label_text, halign=Gtk.Align.START)
        label_container.pack_start(label, False, False, 0)

        if description:
            desc_label = styled(
                Gtk.Label(
                    label=description,
                    halign=Gtk.Align.START,
                    wrap=True,
                    max_width_chars=40,
                ),
                "caption",
                "dim-label",
            )
            label_container.pack_start(desc_label, False, False, 0)

        row_box.pack_start(label_container, False, False, 0)

        # Right side - widget
        widget.set_halign(Gtk.Align.START)
        widget.set_valign(Gtk.Align.START)
        row_box.pack_start(widget, False, False, 0)

        parent.pack_start(row_box, False, False, 0)

    def _add_general_section(self, parent: Gtk.Box) -> None:
        """Add general settings section"""
        self._add_section_header(parent, "General")

        # Launch at login
        autostart_switch = Gtk.Switch(
            active=self.autostart_pref.is_enabled(), sensitive=self.autostart_pref.can_start()
        )
        autostart_switch.connect("notify::active", self._on_autostart_toggled)

        desc = 'Enabling this will disable the "Daemonless mode" option.' if self.settings.daemonless else ""
        self._add_setting_row(parent, "Launch at login", autostart_switch, desc)

        # Hotkey
        if HotkeyController.is_supported():
            hotkey_button = Gtk.Button.new_with_label("Set hotkey")
            hotkey_button.connect("clicked", self._on_hotkey_clicked)
            self._add_setting_row(parent, "Hotkey", hotkey_button)
        else:
            warning_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            warning_text = (
                "Ulauncher doesn't support setting global shortcuts for your desktop environment.\n"
                "Bind this command in your DE settings: gapplication launch io.ulauncher.Ulauncher"
            )
            warning_label = styled(Gtk.Label(label=warning_text, wrap=True, halign=Gtk.Align.START), "caption")
            warning_box.pack_start(warning_label, False, False, 0)
            self._add_setting_row(parent, "Hotkey", warning_box)

        # Color theme
        theme_combo = Gtk.ComboBoxText()
        themes = get_themes()
        for theme in themes:
            theme_combo.append(theme, theme)
        theme_combo.set_active_id(self.settings.theme_name)
        theme_combo.connect("changed", self._on_theme_changed)
        self._add_setting_row(parent, "Color theme", theme_combo)

        # Screen to show on
        screen_combo = Gtk.ComboBoxText()
        screen_combo.append("mouse-pointer-monitor", "The screen with the mouse pointer")
        screen_combo.append("default-monitor", "The default screen")
        screen_combo.set_active_id(self.settings.render_on_screen)
        screen_combo.connect("changed", self._on_screen_changed)
        self._add_setting_row(parent, "Screen to show on", screen_combo)

        # Start with blank query
        clear_query_switch = Gtk.Switch(active=self.settings.clear_previous_query)
        clear_query_switch.connect("notify::active", self._on_clear_query_toggled)
        self._add_setting_row(parent, "Start each session with a blank query", clear_query_switch)

        # Close on focus out
        close_focus_switch = Gtk.Switch(active=self.settings.close_on_focus_out)
        close_focus_switch.connect("notify::active", self._on_close_focus_toggled)
        self._add_setting_row(parent, "Close Ulauncher when losing focus", close_focus_switch)

        # Grab mouse pointer
        grab_mouse_switch = Gtk.Switch(active=self.settings.grab_mouse_pointer)
        grab_mouse_switch.connect("notify::active", self._on_grab_mouse_toggled)
        desc = "Prevents losing focus when using focus modes that follows the mouse"
        self._add_setting_row(parent, "Grab mouse pointer focus", grab_mouse_switch, desc)

    def _add_applications_section(self, parent: Gtk.Box) -> None:
        """Add applications settings section"""
        self._add_section_header(parent, "Applications")

        # Enable application mode
        app_mode_switch = Gtk.Switch(active=self.settings.enable_application_mode)
        app_mode_switch.connect("notify::active", self._on_app_mode_toggled)
        desc = "Disable if you only want to use Ulauncher for shortcuts and extensions"
        self._add_setting_row(parent, "Include applications in search", app_mode_switch, desc)

        # Raise if started
        raise_switch = Gtk.Switch(active=self.settings.raise_if_started, sensitive=IS_X11)
        raise_switch.connect("notify::active", self._on_raise_toggled)
        desc = "This feature is only supported on X11 Display Server"

        self._add_setting_row(parent, "Switch to application if already running", raise_switch, desc)

        # Window width
        width_adjustment = Gtk.Adjustment(value=self.settings.base_width, lower=540, upper=2000, step_increment=10)
        width_spin = Gtk.SpinButton(adjustment=width_adjustment)
        width_spin.connect("value-changed", self._on_width_changed)
        desc = "Window width (in pixels). Min: 540, Max: 2000"
        self._add_setting_row(parent, "Window width", width_spin, desc)

        # Recent apps
        recent_adjustment = Gtk.Adjustment(value=self.settings.max_recent_apps, lower=0, upper=20, step_increment=1)
        recent_spin = Gtk.SpinButton(adjustment=recent_adjustment)
        recent_spin.connect("value-changed", self._on_recent_apps_changed)
        self._add_setting_row(parent, "Number of frequent apps to show", recent_spin)

    def _add_advanced_section(self, parent: Gtk.Box) -> None:
        """Add advanced settings section"""
        self._add_section_header(parent, "Advanced")

        # Show tray icon
        tray_switch = Gtk.Switch(active=self.settings.show_tray_icon)
        tray_switch.connect("notify::active", self._on_tray_toggled)
        desc = "Requires optional dependency AppIndicator3 or XApp (X11 only)"
        self._add_setting_row(parent, "Show tray icon", tray_switch, desc)

        # Desktop filters
        filters_switch = Gtk.Switch(active=self.settings.disable_desktop_filters)
        filters_switch.connect("notify::active", self._on_filters_toggled)
        desc = "Display all applications, even if they are configured to not show in the current desktop environment"
        self._add_setting_row(parent, "Include foreign desktop apps", filters_switch, desc)

        # Daemonless mode
        daemonless_switch = Gtk.Switch(active=self.settings.daemonless)
        daemonless_switch.connect("notify::active", self._on_daemonless_toggled)
        desc = (
            "Prevents keeping Ulauncher running in the background. This mode comes with "
            "some caveats and is not recommended."
        )
        self._add_setting_row(parent, "Daemonless mode", daemonless_switch, desc)

        # Jump keys
        jump_entry = Gtk.Entry(text=self.settings.jump_keys, width_chars=50)
        jump_entry.connect("changed", self._on_jump_keys_changed)
        desc = "Set the keys to use for quickly jumping to results"
        self._add_setting_row(parent, "Jump keys", jump_entry, desc)

        # Terminal command
        terminal_entry = Gtk.Entry(text=self.settings.terminal_command, width_chars=50)
        terminal_entry.connect("changed", self._on_terminal_changed)
        desc = (
            "Overrides terminal for apps that are configured to be run from a terminal. "
            "Set to empty for default terminal"
        )
        self._add_setting_row(parent, "Terminal command", terminal_entry, desc)

    # Event handlers
    def _on_autostart_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        is_enabled = switch.get_active()
        try:
            self.autostart_pref.toggle(is_enabled)
            if is_enabled and self.settings.daemonless:
                self.settings.save({"daemonless": False})
        except Exception:
            logger.exception("Failed to toggle autostart")
            switch.set_active(not is_enabled)

    def _on_hotkey_clicked(self, _: Gtk.Button) -> None:
        HotkeyController.show_dialog()

    def _on_theme_changed(self, combo: Gtk.ComboBoxText) -> None:
        theme_name = combo.get_active_text()
        if theme_name:
            self.settings.save({"theme_name": theme_name})

    def _on_screen_changed(self, combo: Gtk.ComboBoxText) -> None:
        screen = combo.get_active_id()
        if screen:
            self.settings.save({"render_on_screen": screen})

    def _on_clear_query_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        self.settings.save({"clear_previous_query": switch.get_active()})

    def _on_close_focus_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        self.settings.save({"close_on_focus_out": switch.get_active()})

    def _on_grab_mouse_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        self.settings.save({"grab_mouse_pointer": switch.get_active()})

    def _on_app_mode_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        self.settings.save({"enable_application_mode": switch.get_active()})

    def _on_raise_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        self.settings.save({"raise_if_started": switch.get_active()})

    def _on_width_changed(self, spin: Gtk.SpinButton) -> None:
        min_width = 540
        max_width = 2000
        width = spin.get_value_as_int()
        if min_width <= width <= max_width:
            self.settings.save({"base_width": width})

    def _on_recent_apps_changed(self, spin: Gtk.SpinButton) -> None:
        count = spin.get_value_as_int()
        self.settings.save({"max_recent_apps": count})

    def _on_tray_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        is_enabled = switch.get_active()
        self.settings.save({"show_tray_icon": is_enabled})
        events.emit("app:toggle_tray_icon", is_enabled)

    def _on_filters_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        self.settings.save({"disable_desktop_filters": switch.get_active()})

    def _on_daemonless_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        is_enabled = switch.get_active()
        self.settings.save({"daemonless": is_enabled})
        events.emit("app:toggle_hold", not is_enabled)
        if is_enabled:
            SystemdController("ulauncher").stop()

    def _on_jump_keys_changed(self, entry: Gtk.Entry) -> None:
        self.settings.save({"jump_keys": entry.get_text()})

    def _on_terminal_changed(self, entry: Gtk.Entry) -> None:
        self.settings.save({"terminal_command": entry.get_text()})
