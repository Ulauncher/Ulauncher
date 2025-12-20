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

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.settings: Settings = Settings.load()
        self.autostart_pref: SystemdController = SystemdController("ulauncher")

        scrolled = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        scrolled.set_propagate_natural_width(True)
        scrolled.set_propagate_natural_height(True)
        self.pack_start(scrolled, True, True, 0)

        # Create main container - centers on wide screens, fills on narrow screens
        prefs_view = styled(
            Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=30, spacing=24),
            "preferences-content",
        )
        prefs_view.set_halign(Gtk.Align.CENTER)
        prefs_view.set_valign(Gtk.Align.START)
        prefs_view.set_size_request(600, -1)  # min-width of 600px
        scrolled.add(prefs_view)

        # Add sections
        self._add_general_section(prefs_view)
        self._add_applications_section(prefs_view)
        self._add_advanced_section(prefs_view)

    def _add_section_header(self, parent: Gtk.Box, title: str) -> None:
        """Add a section header"""
        label = Gtk.Label(
            label=title,
            halign=Gtk.Align.START,
            margin_top=10,
            margin_bottom=2,
        )
        styled(label, "preferences-section-title")
        parent.pack_start(label, False, False, 0)

    def _create_section_container(self, parent: Gtk.Box, title: str) -> Gtk.Box:
        """Create a stylized section card"""
        self._add_section_header(parent, title)
        section_box = styled(
            Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, margin_top=0),
            "preferences-section-card",
        )
        parent.pack_start(section_box, False, False, 0)
        return section_box

    def _add_setting_row(
        self,
        parent: Gtk.Box,
        label_text: str,
        widget: Gtk.Widget,
        description: str,
        full_width: bool = False,
        is_warning: bool = False,
    ) -> None:
        """Add a settings row with label and widget

        Args:
            parent: The parent container
            label_text: The setting label
            widget: The control widget
            description: Description text
            full_width: If True, widget takes full width below label (for long inputs like Entry)
            is_warning: If True, style the description as a warning using GTK's 'warning' class
        """
        row_box = styled(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24), "preferences-setting-row")
        row_box.set_hexpand(True)

        # Left side - label and description
        label_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        if not full_width:
            label_container.set_hexpand(True)
        else:
            label_container.set_size_request(360, -1)

        label = styled(Gtk.Label(label=label_text, halign=Gtk.Align.START), "preferences-setting-title")
        label.set_xalign(0.0)
        label_container.pack_start(label, False, False, 0)

        desc_label = styled(
            Gtk.Label(
                label=description,
                halign=Gtk.Align.START,
                wrap=True,
                max_width_chars=70,
                margin_top=2,
            ),
            "preferences-setting-description",
        )
        desc_label.set_xalign(0.0)
        if is_warning:
            desc_label.get_style_context().add_class("warning-label")
        label_container.pack_start(desc_label, False, False, 0)

        if full_width:
            # For long inputs: stack vertically
            container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            container.pack_start(label_container, False, False, 0)
            widget.set_halign(Gtk.Align.FILL)
            widget.set_hexpand(True)
            container.pack_start(widget, False, False, 0)
            row_box.pack_start(container, True, True, 0)
        else:
            # For buttons/switches/combos: place on right side
            row_box.pack_start(label_container, True, True, 0)
            widget.set_halign(Gtk.Align.END)
            widget.set_valign(Gtk.Align.START)
            row_box.pack_start(widget, False, False, 0)

        parent.pack_start(row_box, False, False, 0)

    def _add_general_section(self, parent: Gtk.Box) -> None:
        """Add general settings section"""
        general_box = self._create_section_container(parent, "General")

        # Launch at login
        if self.autostart_pref.can_start():
            autostart_switch = Gtk.Switch(active=self.autostart_pref.is_enabled())
            autostart_switch.connect("notify::active", self._on_autostart_toggled)

            desc = "Start Ulauncher automatically whenever your desktop session begins."
            if self.settings.daemonless:
                desc += " Enabling this will turn off Daemonless mode."
            self._add_setting_row(general_box, "Launch at login", autostart_switch, desc)
        else:
            warning_text = (
                "Automatic startup via systemd is not available on your system. "
                "To start Ulauncher at login, add it to your desktop environment's autostart settings."
            )
            unavailable_label = Gtk.Label(label="Not available", sensitive=False)
            self._add_setting_row(general_box, "Launch at login", unavailable_label, warning_text, is_warning=True)

        # Hotkey
        if HotkeyController.is_supported():
            hotkey_button = Gtk.Button.new_with_label("Set hotkey")
            hotkey_button.connect("clicked", self._on_hotkey_clicked)
            hotkey_desc = "Choose the global keyboard shortcut that opens Ulauncher."
            self._add_setting_row(general_box, "Hotkey", hotkey_button, hotkey_desc)
        else:
            warning_text = (
                "Ulauncher doesn't support setting global shortcuts for your desktop environment. "
                "Bind this command in your DE settings: gapplication launch io.ulauncher.Ulauncher"
            )
            unavailable_label = Gtk.Label(label="Not available", sensitive=False)
            self._add_setting_row(general_box, "Hotkey", unavailable_label, warning_text, is_warning=True)

        # Color theme
        theme_combo = Gtk.ComboBoxText()
        themes = get_themes()
        for theme in themes:
            theme_combo.append(theme, theme)
        theme_combo.set_active_id(self.settings.theme_name)
        theme_combo.connect("changed", self._on_theme_changed)
        theme_desc = "Switch between installed themes. Changes apply immediately when you relaunch the UI."
        self._add_setting_row(general_box, "Color theme", theme_combo, theme_desc)

        # Screen to show on
        screen_combo = Gtk.ComboBoxText()
        screen_combo.append("mouse-pointer-monitor", "The screen with the mouse pointer")
        screen_combo.append("default-monitor", "The default screen")
        screen_combo.set_active_id(self.settings.render_on_screen)
        screen_combo.connect("changed", self._on_screen_changed)
        screen_desc = "Decide which monitor presents Ulauncher when you press the hotkey."
        self._add_setting_row(general_box, "Screen to show on", screen_combo, screen_desc)

        # Start with blank query
        clear_query_switch = Gtk.Switch(active=self.settings.clear_previous_query)
        clear_query_switch.connect("notify::active", self._on_clear_query_toggled)
        clear_desc = "Clear the previous search so each invocation starts from an empty input field."
        self._add_setting_row(general_box, "Start each session with a blank query", clear_query_switch, clear_desc)

        # Close on focus out
        close_focus_switch = Gtk.Switch(active=self.settings.close_on_focus_out)
        close_focus_switch.connect("notify::active", self._on_close_focus_toggled)
        focus_desc = "Hide the Ulauncher window automatically as soon as another app grabs focus."
        self._add_setting_row(general_box, "Close Ulauncher when losing focus", close_focus_switch, focus_desc)

        # Grab mouse pointer
        grab_mouse_switch = Gtk.Switch(active=self.settings.grab_mouse_pointer)
        grab_mouse_switch.connect("notify::active", self._on_grab_mouse_toggled)
        grab_desc = "Capture the pointer to prevent focus-follows-mouse setups from stealing the launcher focus."
        self._add_setting_row(general_box, "Grab mouse pointer focus", grab_mouse_switch, grab_desc)

    def _add_applications_section(self, parent: Gtk.Box) -> None:
        """Add applications settings section"""
        applications_box = self._create_section_container(parent, "Applications")

        # Enable application mode
        app_mode_switch = Gtk.Switch(active=self.settings.enable_application_mode)
        app_mode_switch.connect("notify::active", self._on_app_mode_toggled)
        desc = "Include desktop applications alongside shortcuts and extensions in search results."
        self._add_setting_row(applications_box, "Include applications in search", app_mode_switch, desc)

        # Raise if started
        raise_switch = Gtk.Switch(active=self.settings.raise_if_started, sensitive=IS_X11)
        raise_switch.connect("notify::active", self._on_raise_toggled)
        desc = "Focus an already running application instead of launching a duplicate instance. Works only on X11."

        self._add_setting_row(applications_box, "Switch to application if already running", raise_switch, desc)

        # Window width
        width_adjustment = Gtk.Adjustment(value=self.settings.base_width, lower=540, upper=2000, step_increment=10)
        width_spin = Gtk.SpinButton(adjustment=width_adjustment)
        width_spin.connect("value-changed", self._on_width_changed)
        desc = "Set the launcher width between 540 and 2000 pixels to match your workspace."
        self._add_setting_row(applications_box, "Window width", width_spin, desc)

        # Recent apps
        recent_adjustment = Gtk.Adjustment(value=self.settings.max_recent_apps, lower=0, upper=20, step_increment=1)
        recent_spin = Gtk.SpinButton(adjustment=recent_adjustment)
        recent_spin.connect("value-changed", self._on_recent_apps_changed)
        desc = "Control how many frequently used applications remain pinned near the top of the results."
        self._add_setting_row(applications_box, "Number of frequent apps to show", recent_spin, desc)

    def _add_advanced_section(self, parent: Gtk.Box) -> None:
        """Add advanced settings section"""
        advanced_box = self._create_section_container(parent, "Advanced")

        # Show tray icon
        tray_switch = Gtk.Switch(active=self.settings.show_tray_icon)
        tray_switch.connect("notify::active", self._on_tray_toggled)
        desc = "Display a tray icon for quick actions. Requires AppIndicator3 or XApp on X11."
        self._add_setting_row(advanced_box, "Show tray icon", tray_switch, desc)

        # Desktop filters
        filters_switch = Gtk.Switch(active=self.settings.disable_desktop_filters)
        filters_switch.connect("notify::active", self._on_filters_toggled)
        desc = "Show applications that are hidden for your desktop environment by ignoring desktop filters."
        self._add_setting_row(advanced_box, "Include foreign desktop apps", filters_switch, desc)

        # Daemonless mode
        daemonless_switch = Gtk.Switch(active=self.settings.daemonless)
        daemonless_switch.connect("notify::active", self._on_daemonless_toggled)
        desc = (
            "Only run Ulauncher on demand without a background daemon. Startup may be slower and quick launch "
            "features like auto-start are disabled."
        )
        self._add_setting_row(advanced_box, "Daemonless mode", daemonless_switch, desc)

        # Jump keys
        jump_entry = Gtk.Entry(text=self.settings.jump_keys, width_chars=50)
        jump_entry.connect("changed", self._on_jump_keys_changed)
        desc = "Configure the characters used for jumping directly to a result with modifier shortcuts."
        self._add_setting_row(advanced_box, "Jump keys", jump_entry, desc, full_width=True)

        # Terminal command
        terminal_entry = Gtk.Entry(text=self.settings.terminal_command, width_chars=50)
        terminal_entry.connect("changed", self._on_terminal_changed)
        desc = (
            "Override the terminal binary for desktop entries that request a terminal. Leave blank to use the default."
        )
        self._add_setting_row(advanced_box, "Terminal command", terminal_entry, desc, full_width=True)

    # Event handlers
    def _on_autostart_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        is_enabled = switch.get_active()
        try:
            self.autostart_pref.toggle(is_enabled)
            if is_enabled and self.settings.daemonless:
                self.settings.save({"daemonless": False})
        except (OSError, PermissionError, FileNotFoundError):
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
