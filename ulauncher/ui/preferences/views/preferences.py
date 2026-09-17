from __future__ import annotations

import logging
from typing import Any, Callable

from gi.repository import GLib, Gtk, Pango

from ulauncher.ui.helpers.hotkey_controller import HotkeyController
from ulauncher.ui.helpers.theme import get_theme_source, get_themes
from ulauncher.ui.preferences.views import BaseView, styled
from ulauncher.utils.environment import IS_X11
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.settings import Settings
from ulauncher.utils.systemd_controller import SystemdController

logger = logging.getLogger(__name__)
events = EventBus()

THEME_SOURCE_MAX_CHARS = 50


def _theme_label_markup(name: str, source: str) -> str:
    """A theme's name, with its dimmed, smaller source on a second line."""
    label = GLib.markup_escape_text(name)
    label += f'\n<span size="x-small" alpha="55%">{GLib.markup_escape_text(source)}</span>'
    return label


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
                use_markup=True,
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

    def _add_switch_row(
        self,
        parent: Gtk.Box,
        label_text: str,
        description: str,
        active: bool,
        handler: Callable[..., None],
        sensitive: bool = True,
    ) -> Gtk.Switch:
        switch = Gtk.Switch(active=active, sensitive=sensitive)
        switch.connect("notify::active", handler)
        self._add_setting_row(parent, label_text, switch, description)
        return switch

    def _add_spin_row(
        self,
        parent: Gtk.Box,
        label_text: str,
        description: str,
        value: float,
        lower: float,
        upper: float,
        handler: Callable[..., None],
        step_increment: float = 1,
    ) -> Gtk.SpinButton:
        adjustment = Gtk.Adjustment(value=value, lower=lower, upper=upper, step_increment=step_increment)
        spin = Gtk.SpinButton(adjustment=adjustment)
        spin.connect("value-changed", handler)
        self._add_setting_row(parent, label_text, spin, description)
        return spin

    def _add_entry_row(
        self, parent: Gtk.Box, label_text: str, description: str, text: str, handler: Callable[..., None]
    ) -> Gtk.Entry:
        entry = Gtk.Entry(text=text, width_chars=50)
        entry.connect("changed", handler)
        self._add_setting_row(parent, label_text, entry, description, full_width=True)
        return entry

    def _add_general_section(self, parent: Gtk.Box) -> None:
        """Add general settings section"""
        general_box = self._create_section_container(parent, "General")
        self._add_run_in_background_row(general_box)
        self._add_tray_icon_row(general_box)
        self._add_hotkey_row(general_box)
        self._add_setting_row(
            general_box,
            "Color theme",
            self._create_theme_combo(),
            "Switch between installed themes. Changes apply immediately when you relaunch the UI.",
        )
        self._add_setting_row(
            general_box,
            "Screen to show on",
            self._create_screen_combo(),
            "Decide which monitor presents Ulauncher when you press the hotkey.",
        )
        self._add_switch_row(
            general_box,
            "Auto-resume unfinished sessions",
            "If you close Ulauncher without running the query, restore it on the next session.",
            self.settings.auto_resume,
            self._on_auto_resume_toggled,
        )
        self._add_switch_row(
            general_box,
            "Close Ulauncher when losing focus",
            "Hide the Ulauncher window automatically as soon as another app grabs focus.",
            self.settings.close_on_focus_out,
            self._on_close_focus_toggled,
        )
        self._add_switch_row(
            general_box,
            "Grab mouse pointer focus",
            "Capture the pointer to prevent focus-follows-mouse setups from stealing the launcher focus.",
            self.settings.grab_mouse_pointer,
            self._on_grab_mouse_toggled,
        )

    def _create_theme_combo(self) -> Gtk.ComboBox:
        """Theme picker showing each theme's source as a dimmed second line.

        Not ComboBoxText: the source needs markup, and the active id stays the plain theme name.
        """
        theme_store = Gtk.ListStore(str, str)
        for name, theme in get_themes().items():
            theme_store.append([name, _theme_label_markup(name, get_theme_source(theme))])

        combo = Gtk.ComboBox(model=theme_store)
        combo.set_id_column(0)
        # A list combo offsets the popup to the selected row, leaving a blank strip above the
        # first row. A wrap width picks GTK's plain place-below-the-widget path instead.
        combo.set_wrap_width(1)
        renderer = Gtk.CellRendererText()
        # Let the cell grow to a readable width, then middle-ellipsize each line (the name and the source)
        renderer.set_property("ellipsize", Pango.EllipsizeMode.MIDDLE)
        renderer.set_property("max-width-chars", THEME_SOURCE_MAX_CHARS)
        combo.pack_start(renderer, False)
        combo.add_attribute(renderer, "markup", 1)
        combo.set_active_id(self.settings.theme_name)
        combo.connect("changed", self._on_theme_changed)
        return combo

    def _create_screen_combo(self) -> Gtk.ComboBoxText:
        combo = Gtk.ComboBoxText()
        combo.append("mouse-pointer-monitor", "The screen with the mouse pointer")
        combo.append("default-monitor", "The default screen")
        combo.set_wrap_width(1)
        combo.set_active_id(self.settings.render_on_screen)
        combo.connect("changed", self._on_screen_changed)
        return combo

    def _add_applications_section(self, parent: Gtk.Box) -> None:
        """Add applications settings section"""
        applications_box = self._create_section_container(parent, "Applications")
        self._add_switch_row(
            applications_box,
            "Include applications in search",
            "Include desktop applications alongside shortcuts and extensions in search results.",
            self.settings.enable_application_mode,
            self._on_app_mode_toggled,
        )
        self._add_switch_row(
            applications_box,
            "Switch to application if already running",
            "Focus an already running application instead of launching a duplicate instance. Works only on X11.",
            self.settings.raise_if_started,
            self._on_raise_toggled,
            sensitive=IS_X11,
        )
        self._add_spin_row(
            applications_box,
            "Window width",
            "Set the launcher width between 540 and 2000 pixels to match your workspace.",
            self.settings.base_width,
            540,
            2000,
            self._on_width_changed,
            step_increment=10,
        )
        self._add_spin_row(
            applications_box,
            "Number of frequent apps to show",
            "Control how many frequently used applications remain pinned near the top of the results.",
            self.settings.max_recent_apps,
            0,
            20,
            self._on_recent_apps_changed,
        )

    def _add_advanced_section(self, parent: Gtk.Box) -> None:
        """Add advanced settings section"""
        advanced_box = self._create_section_container(parent, "Advanced")
        self._add_switch_row(
            advanced_box,
            "Include foreign desktop apps",
            "Show applications that are hidden for your desktop environment by ignoring desktop filters.",
            self.settings.disable_desktop_filters,
            self._on_filters_toggled,
        )
        self._add_spin_row(
            advanced_box,
            "Window shadow size",
            "The window shadow size. Set to 0 to disable. "
            "Shadows are also disabled if we detect your window manager cannot support them.",
            self.settings.window_shadow,
            0,
            25,
            self._on_shadow_changed,
        )
        self._add_switch_row(
            advanced_box,
            "Enable Layer Shell",
            "Use Layer Shell for positioning on Wayland (when supported). "
            "Recommended unless your desktop handles Wayland positioning separately (Hyprland)",
            self.settings.layer_shell,
            self._on_layer_toggled,
            sensitive=not IS_X11,
        )
        self._add_entry_row(
            advanced_box,
            "Jump keys",
            "Configure the characters used for jumping directly to a result with modifier shortcuts.",
            self.settings.jump_keys,
            self._on_jump_keys_changed,
        )
        self._add_entry_row(
            advanced_box,
            "Terminal command",
            "Override the terminal binary for desktop entries that request a terminal. Leave blank to use the default.",
            self.settings.terminal_command,
            self._on_terminal_changed,
        )

    def _add_run_in_background_row(self, parent: Gtk.Box) -> None:
        # Systemd autostart when available, otherwise a keep-alive fallback switch.
        footer = "\n<b>Recommended:</b> Enabling this will make Ulauncher open noticeably faster."
        autostart_status = self.autostart_pref.status()
        if autostart_status.can_start:
            self._add_switch_row(
                parent,
                "Run in background",
                f"Start Ulauncher automatically with your desktop session so it's ready when you need it.{footer}",
                autostart_status.is_enabled,
                self._on_autostart_toggled,
            )
        else:
            self._add_switch_row(
                parent,
                "Run in background",
                f"Keep Ulauncher running in the background after first use so it stays ready{footer}",
                self.settings.keep_alive,
                self._on_keep_alive_toggled,
            )

    def _add_tray_icon_row(self, parent: Gtk.Box) -> None:
        # Placed next to "Run in background" because the tray icon is only effective while persistent.
        self._tray_switch = self._add_switch_row(
            parent,
            "Show tray icon",
            "Display a tray icon for quick actions. Only available while Ulauncher is set to "
            "run in the background. Also requires AppIndicator3 or XApp on X11.",
            self.settings.show_tray_icon,
            self._on_tray_toggled,
            sensitive=self.settings.is_persistent(),
        )

    def _add_hotkey_row(self, parent: Gtk.Box) -> None:
        if HotkeyController.is_supported():
            hotkey_button = Gtk.Button.new_with_label("Set hotkey")
            hotkey_button.connect("clicked", self._on_hotkey_clicked)
            desc = "Choose the global keyboard shortcut that opens Ulauncher."
            self._add_setting_row(parent, "Hotkey", hotkey_button, desc)
        else:
            warning_text = (
                "Ulauncher doesn't support setting global shortcuts for your desktop environment. "
                "Bind this command in your DE settings: gapplication launch io.ulauncher.Ulauncher"
            )
            unavailable_label = Gtk.Label(label="Not available", sensitive=False)
            self._add_setting_row(parent, "Hotkey", unavailable_label, warning_text, is_warning=True)

    # Event handlers
    def _on_autostart_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        is_enabled = switch.get_active()
        # Skip if already in sync - notably when set_active() below re-fires this handler.
        if is_enabled == self.autostart_pref.status().is_enabled:
            return
        try:
            self.autostart_pref.toggle(is_enabled)
        except OSError:
            logger.exception("Failed to toggle autostart")
            switch.set_active(not is_enabled)
            return
        self._tray_switch.set_sensitive(is_enabled)
        events.emit("app:toggle_hold", is_enabled)

    def _on_hotkey_clicked(self, _: Gtk.Button) -> None:
        HotkeyController.show_dialog()

    def _on_theme_changed(self, combo: Gtk.ComboBox) -> None:
        theme_name = combo.get_active_id()
        if theme_name:
            self.settings.save({"theme_name": theme_name})

    def _on_screen_changed(self, combo: Gtk.ComboBoxText) -> None:
        screen = combo.get_active_id()
        if screen:
            self.settings.save({"render_on_screen": screen})

    def _on_auto_resume_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        self.settings.save({"auto_resume": switch.get_active()})

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

    def _on_shadow_changed(self, spin: Gtk.SpinButton) -> None:
        self.settings.save({"window_shadow": spin.get_value_as_int()})

    def _on_layer_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        self.settings.save({"layer_shell": switch.get_active()})

    def _on_tray_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        is_enabled = switch.get_active()
        self.settings.save({"show_tray_icon": is_enabled})
        events.emit("app:toggle_tray_icon", is_enabled)

    def _on_filters_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        self.settings.save({"disable_desktop_filters": switch.get_active()})

    def _on_keep_alive_toggled(self, switch: Gtk.Switch, _: Any) -> None:
        is_enabled = switch.get_active()
        self.settings.save({"keep_alive": is_enabled})
        self._tray_switch.set_sensitive(is_enabled)
        events.emit("app:toggle_hold", is_enabled)

    def _on_jump_keys_changed(self, entry: Gtk.Entry) -> None:
        self.settings.save({"jump_keys": entry.get_text()})

    def _on_terminal_changed(self, entry: Gtk.Entry) -> None:
        self.settings.save({"terminal_command": entry.get_text()})
