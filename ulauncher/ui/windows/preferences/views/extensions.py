from __future__ import annotations

import contextlib
import logging
from typing import Any, Literal

from gi.repository import GLib, Gtk

from ulauncher.modes.extensions import extension_registry
from ulauncher.modes.extensions.extension_controller import (
    ExtensionController,
    ExtensionNotFoundError,
    ExtensionPreference,
)
from ulauncher.ui.windows.preferences import views
from ulauncher.ui.windows.preferences.utils import ext_utils
from ulauncher.ui.windows.preferences.utils.ext_handlers import ExtensionHandlers
from ulauncher.ui.windows.preferences.views import (
    SIDEBAR_WIDTH,
    BaseView,
    DataListBoxRow,
    TextArea,
    start_spinner_button_animation,
    styled,
)
from ulauncher.utils.launch_detached import open_detached
from ulauncher.utils.load_icon_surface import load_icon_surface

logger = logging.getLogger()
REFRESH_INTERVAL = 250


class ExtensionsView(BaseView):
    extension_cache: dict[str, tuple[str, ext_utils.ExtStatus, str | None]] = {}
    active_ext: ExtensionController | None = None
    keyword_inputs: dict[str, Gtk.Entry] = {}
    pref_widgets: dict[str, Gtk.CheckButton | Gtk.SpinButton | Gtk.Entry | Gtk.ComboBoxText | TextArea] = {}
    ext_details_view: Gtk.Box
    save_button: Gtk.Button | None = None

    def __init__(self, window: Gtk.Window) -> None:
        super().__init__(window, orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, halign=Gtk.Align.FILL)

        # Initialize extension handlers
        self.handlers = ExtensionHandlers(window)

        left_sidebar = styled(
            Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, hexpand=False, halign=Gtk.Align.START, width_request=SIDEBAR_WIDTH
            ),
            "sidebar",
        )

        # Action buttons at top (horizontal layout)
        header_button_box = styled(
            Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5, homogeneous=True), "toolbar"
        )

        buttons = [
            ("Add extension", "list-add-symbolic", self._on_add_extension),
            ("Discover extensions", "web-browser-symbolic", lambda _: open_detached("https://ext.ulauncher.io")),
            (
                "Extension API documentation",
                "help-contents-symbolic",
                lambda _: open_detached("https://docs.ulauncher.io"),
            ),
        ]

        for label, icon_name, callback in buttons:
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.SMALL_TOOLBAR)
            button = Gtk.Button(margin=8, image=icon, tooltip_text=label)

            button.connect("clicked", callback)
            header_button_box.pack_start(button, True, True, 0)

        left_sidebar.pack_start(header_button_box, False, False, 0)

        # Scrolled window for extensions list
        scrolled_left = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)

        self.listbox_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scrolled_left.add(self.listbox_container)

        left_sidebar.pack_start(scrolled_left, True, True, 0)

        self.pack_start(left_sidebar, False, False, 0)

        # Right side - extension details
        self.ext_details_view = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, margin=10, hexpand=True, halign=Gtk.Align.FILL
        )
        self._reset_extension_view()

        self.pack_start(self.ext_details_view, True, True, 0)

        def reload_extension_list() -> Literal[True]:
            self._load_extension_list()
            return True

        # We need to reload extension state periodically to reflect changes
        # - The initial runtime state is misleading/confusing "stopped" before they have started
        # - If they are killed by task/oom killer
        # - If they are installed or uninstalled by the CLI
        GLib.timeout_add(REFRESH_INTERVAL, reload_extension_list)

    def _list_has_changes(self) -> bool:
        extension_cache: dict[str, tuple[str, ext_utils.ExtStatus, str | None]] = {}

        for ext in extension_registry.iterate():
            if not ext.shadowed_by_preview:
                extension_cache[ext.id] = (
                    ext.manifest.name,
                    ext_utils.get_status_str(ext),
                    ext.get_normalized_icon_path(),
                )

        if extension_cache == self.extension_cache:
            return False

        self.extension_cache = extension_cache
        return True

    def _load_extension_list(self) -> None:
        """Load extensions from registry"""

        if not self._list_has_changes():
            return

        # (re)create extensions_listbox
        extensions_listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)

        for ext_id, (name, status, icon_path) in self.extension_cache.items():
            row = self._create_extension_row(ext_id, name, status, icon_path)
            extensions_listbox.add(row)
            if self.active_ext and self.active_ext.id == ext_id:
                extensions_listbox.select_row(row)

        if not self.extension_cache:
            # Show empty state
            empty_label = styled(
                Gtk.Label(label="No extensions installed", margin_top=30, margin_bottom=30), "caption", "dim-label"
            )
            placeholder_row = Gtk.ListBoxRow(selectable=False, activatable=False)
            placeholder_row.add(empty_label)
            extensions_listbox.add(placeholder_row)

        # Clear old listbox and replace with new one
        for child in self.listbox_container.get_children():
            self.listbox_container.remove(child)
        self.listbox_container.pack_start(extensions_listbox, True, True, 0)
        extensions_listbox.show_all()

        # Connect signal (must happen after setting the initial selection)
        extensions_listbox.connect("row-selected", self._on_extension_selected)

    def _create_extension_row(
        self, ext_id: str, name: str, status: ext_utils.ExtStatus, icon_path: str | None
    ) -> DataListBoxRow:
        """Add an extension row to the list"""
        row = DataListBoxRow(ext_id)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin=8)

        # Icon
        icon_surface = load_icon_surface(icon_path, views.ICON_SIZE_S, self.get_scale_factor())
        icon_image = Gtk.Image.new_from_surface(icon_surface)
        box.pack_start(icon_image, False, False, 0)

        name_label = styled(Gtk.Label(label=name, halign=Gtk.Align.START), "body")
        box.pack_start(name_label, True, True, 0)

        status_box = Gtk.Box(spacing=5)
        status_label = styled(
            Gtk.Label(
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
                label=status,
            ),
            "status-badge",
            status,
        )
        status_box.pack_start(status_label, False, False, 0)
        box.pack_start(status_box, False, False, 0)

        row.add(box)
        return row

    def _on_extension_selected(self, _listbox: Gtk.ListBox, row: DataListBoxRow | None) -> None:
        """Handle extension selection"""
        if not row:
            return

        with contextlib.suppress(ExtensionNotFoundError):
            if ext := extension_registry.get(row.id):
                self.active_ext = ext
                self._show_extension_details(ext)

    def _clear_extension_view(self) -> None:
        """Clear the extension details view"""
        for child in self.ext_details_view.get_children():
            self.ext_details_view.remove(child)
        self.save_button = None

    def _reset_extension_view(self) -> None:
        """Clear the extension details view and show placeholder"""
        self._clear_extension_view()

        # Add placeholder text
        placeholder_label = styled(
            Gtk.Label(label="Select an extension to view details", valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER),
            "dim-label",
        )

        self.ext_details_view.pack_start(placeholder_label, True, True, 0)
        self.ext_details_view.show_all()

    def _show_extension_details(self, ext: ExtensionController) -> None:
        """Show details for selected extension"""
        self._clear_extension_view()

        scrolled = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin=10)

        details_box.pack_start(self._create_extension_header(ext), False, False, 0)
        details_box.pack_start(Gtk.Separator(), False, False, 0)
        details_box.pack_start(self._create_installation_instructions_section(ext), False, False, 0)
        details_box.pack_start(self._create_triggers_section(ext), False, False, 0)
        details_box.pack_start(self._create_preferences_section(ext), False, False, 0)
        details_box.pack_start(self._create_error_section(ext), False, False, 0)

        scrolled.add(details_box)
        self.ext_details_view.pack_start(scrolled, True, True, 0)
        self.ext_details_view.show_all()

    def _create_extension_header(self, ext: ExtensionController) -> Gtk.Box:
        """Create the extension header with icon, name, and action buttons"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)

        # Large icon
        icon_path = ext.get_normalized_icon_path()
        icon_surface = load_icon_surface(icon_path, views.ICON_SIZE_XL, self.get_scale_factor())
        icon_image = Gtk.Image.new_from_surface(icon_surface)
        header_box.pack_start(icon_image, False, False, 0)

        # Extension info
        info_box = self._create_extension_info_box(ext)
        header_box.pack_start(info_box, True, True, 0)

        # Action buttons
        button_box = self._create_action_buttons(ext)
        header_box.pack_end(button_box, False, False, 0)

        return header_box

    def _create_extension_info_box(self, ext: ExtensionController) -> Gtk.Box:
        """Create the extension information section"""
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, hexpand=True)

        name_label = styled(Gtk.Label(label=ext.manifest.name, halign=Gtk.Align.START), "title-1")
        info_box.pack_start(name_label, False, False, 0)

        if ext.manifest.authors:
            authors_label = styled(
                Gtk.Label(label=f"by {ext.manifest.authors}", halign=Gtk.Align.START), "caption", "dim-label"
            )
            info_box.pack_start(authors_label, False, False, 0)

        # Repository information
        details_row = styled(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5), "caption", "dim-label")
        info_box.pack_start(details_row, False, False, 0)

        if ext.state.updated_at:
            try:
                updated_date = ext.state.updated_at[:10]
                calendar_icon = Gtk.Image.new_from_icon_name("x-office-calendar-symbolic", Gtk.IconSize.MENU)
                updated_label = Gtk.Label(label=updated_date, halign=Gtk.Align.START)
                details_row.pack_start(calendar_icon, False, False, 0)
                details_row.pack_start(updated_label, False, False, 0)
            except (ValueError, AttributeError):
                pass

        status_text = "User installed" if ext.is_manageable else "Externally managed"
        status_label = Gtk.Label(label=status_text, halign=Gtk.Align.START)
        details_row.pack_start(status_label, False, False, 0)

        return info_box

    def _create_action_buttons(self, ext: ExtensionController) -> Gtk.Box:
        """Create the action buttons section"""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5, valign=Gtk.Align.END)

        # Repository link button
        if ext.state.browser_url and ext.state.browser_url.startswith("http"):
            repo_icon = Gtk.Image.new_from_icon_name("web-browser-symbolic", Gtk.IconSize.BUTTON)
            repo_link = Gtk.Button(image=repo_icon, tooltip_text="Open repository")
            repo_link.connect("clicked", lambda _: open_detached(ext.state.browser_url))
            button_box.pack_start(repo_link, False, False, 0)

        # Folder button
        browse_icon = Gtk.Image.new_from_icon_name("folder-symbolic", Gtk.IconSize.BUTTON)
        folder_button = Gtk.Button(image=browse_icon, tooltip_text="Open extensions directory")
        folder_button.connect("clicked", lambda _: open_detached(ext.path))
        button_box.pack_start(folder_button, False, False, 0)

        # Save button
        save_icon = Gtk.Image.new_from_icon_name("checkmark-symbolic", Gtk.IconSize.BUTTON)
        self.save_button = styled(Gtk.Button(image=save_icon, tooltip_text="Save", sensitive=False), "suggested-action")
        self.save_button.connect("clicked", lambda: self.save_changes())
        button_box.pack_start(self.save_button, False, False, 0)

        # Update button
        if ext.is_manageable and ext.state.url:
            update_icon = Gtk.Image.new_from_icon_name("software-update-symbolic", Gtk.IconSize.BUTTON)
            update_button = styled(Gtk.Button(image=update_icon, tooltip_text="Check updates"), "update-button")
            update_button.connect("clicked", self._on_check_updates, ext)
            button_box.pack_start(update_button, False, False, 0)

        # Remove button
        if ext.is_manageable:
            remove_icon = Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON)
            remove_button = styled(Gtk.Button(image=remove_icon, tooltip_text="Remove"), "destructive-action")
            remove_button.connect("clicked", self.on_remove_extension, ext)
            button_box.pack_start(remove_button, False, False, 0)

        # Enable/Disable toggle
        toggle_switch = Gtk.Switch(
            vexpand=False,
            valign=Gtk.Align.CENTER,
            tooltip_text="Disable" if ext.is_enabled else "Enable",
            active=ext.is_enabled,
        )
        toggle_switch.connect("state-set", self._on_toggle_extension, ext)
        button_box.pack_start(toggle_switch, False, False, 0)

        return button_box

    def _create_installation_instructions_section(self, ext: ExtensionController) -> Gtk.Box:
        """Create the installation instructions section"""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        if ext.manifest.instructions and ext.manifest.instructions.strip():
            instructions_container = styled(
                Gtk.Box(orientation=Gtk.Orientation.VERTICAL), "ext-installation-instructions"
            )

            # Auto-expand if there's an error
            instructions_expander = Gtk.Expander(label="Installation instructions", expanded=ext.has_error)

            # Instructions content with HTML rendering
            instructions_label = Gtk.Label(
                label=ext.manifest.instructions,
                use_markup=True,
                selectable=True,
                margin=10,
                halign=Gtk.Align.START,
                wrap=True,
            )

            instructions_expander.add(instructions_label)
            instructions_container.add(instructions_expander)
            container.pack_start(instructions_container, False, False, 0)

        return container

    def _create_triggers_section(self, ext: ExtensionController) -> Gtk.Box:
        """Create the triggers/keywords section"""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Reset widgets for this extension
        self.keyword_inputs = {}

        for trigger_id, trigger in ext.triggers.items():
            if trigger.keyword:
                trigger_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

                keyword_label = styled(
                    Gtk.Label(label=f"{trigger.name} keyword", use_markup=True, halign=Gtk.Align.START), "body"
                )
                trigger_box.pack_start(keyword_label, False, False, 0)

                # Keyword input field
                keyword_entry = Gtk.Entry(text=trigger.keyword, placeholder_text="Enter keyword...", width_chars=20)
                keyword_entry.connect("changed", self._on_setting_change, self.save_button)
                trigger_box.pack_start(keyword_entry, False, False, 0)

                if trigger.description:
                    footnotes_label = styled(
                        Gtk.Label(label=trigger.description, use_markup=True, halign=Gtk.Align.START),
                        "caption",
                        "dim-label",
                    )
                    trigger_box.pack_start(footnotes_label, False, False, 0)

                # Store widget reference
                self.keyword_inputs[trigger_id] = keyword_entry
                container.pack_start(trigger_box, False, False, 0)

        return container

    def _create_preferences_section(self, ext: ExtensionController) -> Gtk.Box:
        """Create the preferences section"""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Reset widgets for this extension
        self.pref_widgets = {}

        for pref_id, pref in ext.preferences.items():
            pref_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

            pref_name = pref.get("name", pref_id)
            pref_type = pref.get("type", "input")

            if pref_type == "checkbox":
                checkbox = Gtk.CheckButton(label=pref_name, active=pref.get("value", False))
                checkbox.connect("toggled", self._on_setting_change, self.save_button)
                self.pref_widgets[pref_id] = checkbox
                pref_box.pack_start(checkbox, False, False, 0)
            else:
                label = styled(Gtk.Label(label=pref_name, halign=Gtk.Align.START), "body")
                pref_box.pack_start(label, False, False, 0)

                widget = self._create_preference_widget(pref_id, pref, pref_type)
                if widget:
                    pref_box.pack_start(widget, False, False, 0)

            if descr := pref.description:
                desc_label = styled(Gtk.Label(label=descr, halign=Gtk.Align.START, wrap=True), "caption", "dim-label")
                pref_box.pack_start(desc_label, False, False, 0)

            container.pack_start(pref_box, False, False, 0)

        return container

    def _create_preference_widget(self, pref_id: str, pref: ExtensionPreference, pref_type: str) -> Gtk.Widget | None:
        """Create a preference widget based on type"""
        if pref_type == "number":
            adjustment = Gtk.Adjustment(
                value=int(pref.get("value", 0) or 0),
                lower=pref.get("min", 0) or 0,
                upper=pref.get("max", 100) or 100,
                step_increment=1,
            )
            spin = Gtk.SpinButton(adjustment=adjustment)
            spin.connect("value-changed", self._on_setting_change, self.save_button)
            self.pref_widgets[pref_id] = spin
            return spin
        if pref_type == "select":
            return self._create_select_widget(pref_id, pref)
        if pref_type == "text":
            return self._create_text_widget(pref_id, pref)
        if pref_type == "input":
            entry = Gtk.Entry(text=str(pref.get("value", "")))
            entry.connect("changed", self._on_setting_change, self.save_button)
            self.pref_widgets[pref_id] = entry
            return entry

        logger.warning("Unknown preference type: %s", pref_type)
        return None

    def _create_select_widget(self, pref_id: str, pref: ExtensionPreference) -> Gtk.ComboBoxText:
        """Create a select/combo box widget"""
        options = pref.get("options", [])
        current_value = str(pref.get("value", ""))
        active_index = -1
        combo = Gtk.ComboBoxText()

        for i, option in enumerate(options):
            if isinstance(option, dict):
                # Handle object with "text" and "value" keys
                value = str(option.get("value", ""))
                text = option.get("text", value)
                combo.append(value, text)
                if value == current_value:
                    active_index = i
            else:
                # Handle simple string options
                option_str = str(option)
                combo.append_text(option_str)
                if option_str == current_value:
                    active_index = i

        if active_index >= 0:
            combo.set_active(active_index)
        combo.connect("changed", self._on_setting_change, self.save_button)
        self.pref_widgets[pref_id] = combo
        return combo

    def _create_text_widget(self, pref_id: str, pref: ExtensionPreference) -> Gtk.ScrolledWindow:
        """Create a text area widget"""
        scroll_container = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        textview = TextArea(
            top_margin=10, bottom_margin=10, left_margin=10, right_margin=10, wrap_mode=Gtk.WrapMode.WORD
        )
        textview.set_text(str(pref.get("value", "")))
        scroll_container.add(textview)
        textview.get_buffer().connect("changed", self._on_setting_change, self.save_button)
        self.pref_widgets[pref_id] = textview
        return scroll_container

    def _create_error_section(self, ext: ExtensionController) -> Gtk.Box:
        """Create the error display section"""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        if ext.has_error:
            error_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)
            # Create appropriate error message based on type
            message_text = ext_utils.get_error_message(ext.state.error_type, ext.state.error_message, ext)

            # Create warning-style container
            warning_frame = styled(Gtk.Box(), "ext-error-box")

            error_label = Gtk.Label(
                label=message_text,
                use_markup=True,
                halign=Gtk.Align.START,
                wrap=True,
                selectable=True,
                max_width_chars=80,
            )

            error_label.connect("activate-link", lambda _, uri: open_detached(uri))
            warning_frame.pack_start(error_label, False, False, 0)
            error_box.pack_start(warning_frame, False, False, 0)
            container.pack_start(error_box, False, False, 0)

        return container

    def _on_setting_change(self, _widget: Gtk.Widget, save_button: Gtk.Button) -> None:
        save_button.set_sensitive(True)

    def _on_add_extension(self, _widget: Gtk.Widget) -> None:
        def after_add_extension(ext: ExtensionController) -> None:
            self.active_ext = ext
            self._show_extension_details(ext)

        self.handlers.add_extension(after_add_extension)

    def _on_toggle_extension(self, _switch: Gtk.Switch, state: bool, ext: ExtensionController) -> None:
        self.handlers.toggle_extension(state, ext)

    def _on_check_updates(self, button: Gtk.Button, ext: ExtensionController) -> None:
        stop_spinner_button_animation = start_spinner_button_animation(button)

        self.handlers.check_updates(ext, stop_spinner_button_animation)

    def on_remove_extension(self, _button: Gtk.Button, ext: ExtensionController) -> None:
        def after_remove_extension() -> None:
            self.active_ext = None
            self._reset_extension_view()

        self.handlers.remove_extension(ext, after_remove_extension)

    def _get_preferences_from_form(self) -> dict[str, Any] | None:
        """Save both keyword and preference changes"""
        try:
            # Save keyword changes
            keyword_data: dict[str, dict[str, str]] = {}
            for trigger_id, entry in self.keyword_inputs.items():
                new_keyword = entry.get_text().strip()
                if new_keyword:
                    keyword_data[trigger_id] = {"keyword": new_keyword}

            # Save preference changes
            pref_data: dict[str, bool | str | int] = {}
            for pref_id, widget in self.pref_widgets.items():
                if isinstance(widget, Gtk.CheckButton):
                    pref_data[pref_id] = widget.get_active()
                elif isinstance(widget, Gtk.SpinButton):
                    pref_data[pref_id] = widget.get_value_as_int()
                elif isinstance(widget, Gtk.ComboBoxText):
                    # For select type - get the active ID (value) or text if no ID set
                    active_id = widget.get_active_id()
                    if active_id is not None:
                        pref_data[pref_id] = active_id
                    else:
                        pref_data[pref_id] = widget.get_active_text() or ""
                elif isinstance(widget, (Gtk.Entry, TextArea)):
                    pref_data[pref_id] = widget.get_text()

        except Exception:
            logger.exception("Failed to save extension changes")
            return None

        return {"triggers": keyword_data, "preferences": pref_data}

    def save_changes(self) -> bool:
        if self.active_ext and self.save_button and self.save_button.get_sensitive():
            user_prefs = self._get_preferences_from_form()
            if user_prefs:
                self.active_ext.save_user_preferences(user_prefs)
                self.save_button.set_sensitive(False)
                return True
        return False
