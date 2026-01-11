from __future__ import annotations

import logging
from typing import Any

from gi.repository import GLib, Gtk, Pango

from ulauncher.modes.extensions import extension_registry
from ulauncher.modes.extensions.extension_controller import (
    ExtensionController,
    ExtensionPreference,
)
from ulauncher.ui.windows.preferences import views
from ulauncher.ui.windows.preferences.utils import ext_utils
from ulauncher.ui.windows.preferences.utils.ext_handlers import ExtensionHandlers
from ulauncher.ui.windows.preferences.utils.sidebar_layout import SidebarItem, SidebarLayout
from ulauncher.ui.windows.preferences.views import (
    BaseView,
    TextArea,
    get_window_for_widget,
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
    save_button: Gtk.Button | None = None

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, hexpand=True, halign=Gtk.Align.FILL)

        # Initialize extension handlers (pass self so it can call get_toplevel() when needed)
        self.handlers = ExtensionHandlers(self)

        self.layout = SidebarLayout(
            footer_actions=[
                ("Add extension", "list-add-symbolic", self._on_add_extension),
                (
                    "Discover extensions",
                    "system-search-symbolic",
                    lambda _: open_detached("https://ext.ulauncher.io/?versions=2%2C3"),
                ),
                ("Develop your own", "text-x-generic-symbolic", lambda _: open_detached("https://docs.ulauncher.io")),
            ],
        )
        self.pack_start(self.layout, True, True, 0)

        self._load_extension_list()
        self._show_placeholder()

        def reload_extension_list() -> bool:
            # Stop the timeout if the view or its toplevel window is destroyed
            toplevel = get_window_for_widget(self)
            if not toplevel or not toplevel.get_window():
                return False  # Stops the timeout

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

        # Convert extensions to SidebarItems
        items: list[SidebarItem] = []
        for ext_id, (name, status, icon_path) in self.extension_cache.items():
            icon_surface = load_icon_surface(icon_path, views.ICON_SIZE_M, self.get_scale_factor())
            icon_image = Gtk.Image.new_from_surface(icon_surface)

            # Only show status badge if not "on" (enabled extensions don't need a badge)
            display_status = None if status == "on" else status
            status_classes = (status,) if display_status else ()

            item = SidebarItem(
                id=ext_id,
                icon=icon_image,
                name=name,
                label=display_status,
                label_style_classes=status_classes,
                on_activate=self._on_extension_item_activated,
            )
            items.append(item)

        # Set empty placeholder builder for when there are no extensions
        self.layout.set_empty_placeholder_builder(
            lambda: styled(
                Gtk.Label(label="No extensions installed", margin_top=30, margin_bottom=30), "caption", "dim-label"
            )
        )

        active_ext_id = self.active_ext.id if self.active_ext else None
        self.layout.set_items(items, active_ext_id)

    def _on_extension_item_activated(self, item: SidebarItem) -> None:
        """Handle extension selection in sidebar"""
        if ext := extension_registry.get(item.id):
            self.active_ext = ext
            self._show_extension_details(ext)
        else:
            self.active_ext = None
            self._show_placeholder()

    def _show_placeholder(self) -> None:
        """Show placeholder when no extension is selected"""
        self.save_button = None
        has_extensions = bool(self.extension_cache)
        heading = "Select an extension to view details" if has_extensions else "Install your first extension"
        hint = (
            "Choose an extension from the list to configure it."
            if has_extensions
            else "Click the Add Extension button in the sidebar to install an extension."
        )

        placeholder_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            valign=Gtk.Align.CENTER,
            halign=Gtk.Align.CENTER,
            spacing=10,
            margin=30,
        )

        heading_label = styled(Gtk.Label(label=heading, halign=Gtk.Align.CENTER), "title-3")
        hint_label = styled(
            Gtk.Label(label=hint, halign=Gtk.Align.CENTER, wrap=True),
            "body",
            "dim-label",
        )

        placeholder_box.pack_start(heading_label, False, False, 0)
        placeholder_box.pack_start(hint_label, False, False, 0)

        self.layout.set_content(placeholder_box)

    def _show_extension_details(self, ext: ExtensionController) -> None:
        """Show details for selected extension"""
        self.save_button = None

        # Container for fixed header and scrollable content
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Fixed header section
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin=20, margin_bottom=0)
        header_box.pack_start(self._create_extension_header(ext), False, False, 0)
        header_box.pack_start(Gtk.Separator(), False, False, 0)
        container.pack_start(header_box, False, False, 0)

        # Scrollable content section
        scrolled = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin=20, margin_top=15)

        details_box.pack_start(self._create_extension_status_info(ext), False, False, 0)
        details_box.pack_start(self._create_installation_instructions_section(ext), False, False, 0)
        details_box.pack_start(self._create_triggers_section(ext), False, False, 0)
        details_box.pack_start(self._create_preferences_section(ext), False, False, 0)
        details_box.pack_start(self._create_error_section(ext), False, False, 0)

        scrolled.add(details_box)
        container.pack_start(scrolled, True, True, 0)

        self.layout.set_content(container)

    def _create_extension_header(self, ext: ExtensionController) -> Gtk.Box:
        """Create the extension header with icon, name, and action buttons"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        # Left side: Icon and name info
        left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        # Large icon
        icon_path = ext.get_normalized_icon_path()
        icon_surface = load_icon_surface(icon_path, views.ICON_SIZE_L, self.get_scale_factor())
        icon_image = Gtk.Image.new_from_surface(icon_surface)
        left_box.pack_start(icon_image, False, False, 0)

        # Name and secondary info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        name_toggle_box, secondary_info_box = self._create_name_toggle_column(ext)
        info_box.pack_start(name_toggle_box, False, False, 0)
        if secondary_info_box:
            info_box.pack_start(secondary_info_box, False, False, 0)
        left_box.pack_start(info_box, True, True, 0)

        header_box.pack_start(left_box, True, True, 0)

        # Right side: Action buttons - right aligned
        button_box = self._create_header_buttons(ext)
        header_box.pack_end(button_box, False, False, 0)

        return header_box

    def _create_name_toggle_column(self, ext: ExtensionController) -> tuple[Gtk.Box, Gtk.Box | None]:
        """Create the name column content"""
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        name_label = styled(Gtk.Label(label=ext.manifest.name, halign=Gtk.Align.START), "title")
        name_box.pack_start(name_label, False, False, 0)

        # Create a vertical box for authors and updated date
        secondary_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, valign=Gtk.Align.END)

        if ext.manifest.authors:
            authors_label = styled(
                Gtk.Label(label=f"by {ext.manifest.authors}", halign=Gtk.Align.START), "caption", "dim-label"
            )
            secondary_info_box.pack_start(authors_label, False, False, 0)

        # Add updated date (commit time)
        if ext.state.commit_time:
            try:
                updated_date = ext.state.commit_time[:10]
                updated_row = styled(
                    Gtk.Label(label=f"updated on {updated_date}", halign=Gtk.Align.START), "caption", "dim-label"
                )
                secondary_info_box.pack_start(updated_row, False, False, 0)
            except (ValueError, AttributeError):
                pass

        return name_box, secondary_info_box if secondary_info_box.get_children() else None

    def _create_extension_status_info(self, ext: ExtensionController) -> Gtk.Box:
        """Create a centered row with status information"""
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.CENTER, spacing=0)

        # Build parts of the status line
        parts: list[Gtk.Widget] = []

        # Repository URL (if available)
        if ext.state.browser_url and ext.state.browser_url.startswith("http"):
            display_url = ext.state.browser_url.replace("https://", "").replace("http://", "")
            repo_link = Gtk.LinkButton.new_with_label(ext.state.browser_url, display_url)
            repo_link.set_halign(Gtk.Align.CENTER)
            # Enable ellipsis on the internal label to handle long URLs
            label = repo_link.get_child()
            if isinstance(label, Gtk.Label):
                label.set_ellipsize(Pango.EllipsizeMode.END)
            parts.append(repo_link)

        # Installation status
        status_text = "user installed" if ext.is_manageable else "externally managed"
        status_label = styled(Gtk.Label(label=status_text), "caption", "dim-label")
        parts.append(status_label)

        # Open source location link
        folder_link = Gtk.LinkButton.new_with_label(f"file://{ext.path}", "installation location")
        folder_link.set_halign(Gtk.Align.CENTER)
        folder_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        folder_icon = styled(Gtk.Label(label="📁"), "caption")
        folder_box.pack_start(folder_icon, False, False, 0)
        folder_box.pack_start(folder_link, False, False, 0)
        folder_box.set_halign(Gtk.Align.CENTER)
        parts.append(folder_box)

        # Add parts with bullet separators
        for i, part in enumerate(parts):
            if i > 0:
                # Add bullet separator
                bullet = styled(Gtk.Label(label=" • "), "caption", "dim-label")
                container.pack_start(bullet, False, False, 0)
            container.pack_start(part, False, False, 0)

        return container

    def _create_header_buttons(self, ext: ExtensionController) -> Gtk.Box:
        """Create the header action buttons (Toggle, Save, Check Updates, Remove)"""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, valign=Gtk.Align.CENTER)

        # Toggle switch
        toggle_switch = styled(
            Gtk.Switch(
                vexpand=False,
                valign=Gtk.Align.CENTER,
                tooltip_text="Disable" if ext.is_enabled else "Enable",
                active=ext.is_enabled,
            ),
            "small-switch",
        )
        toggle_switch.connect("state-set", self._on_toggle_extension, ext)
        button_box.pack_start(toggle_switch, False, False, 0)

        # Save button
        self.save_button = styled(Gtk.Button(label="Save", sensitive=False), "suggested-action")
        self.save_button.connect("clicked", lambda _: self.save_changes())
        button_box.pack_start(self.save_button, False, False, 0)

        # Check Updates button
        if ext.is_manageable and ext.state.url:
            update_button = Gtk.Button(label="Check Updates")
            update_button.connect("clicked", self._on_check_updates, ext)
            button_box.pack_start(update_button, False, False, 0)

        # Remove button (only if extension is manageable)
        if ext.is_manageable:
            remove_button = styled(Gtk.Button(label="Remove"), "destructive-action")
            remove_button.connect("clicked", self.on_remove_extension, ext)
            button_box.pack_start(remove_button, False, False, 0)

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
                label=ext_utils.autofmt_pango_code_block(ext.manifest.instructions),
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
                keyword_entry.connect("changed", self._on_setting_change)
                trigger_box.pack_start(keyword_entry, False, False, 0)

                if trigger.description:
                    footnotes_label = styled(
                        Gtk.Label(
                            label=ext_utils.autofmt_pango_code_block(trigger.description),
                            use_markup=True,
                            halign=Gtk.Align.START,
                        ),
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
            pref_box = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5), "ext-pref-box")

            pref_name = pref.get("name", pref_id)
            pref_type = pref.get("type", "input")

            if pref_type == "checkbox":
                checkbox = Gtk.CheckButton(label=pref_name, active=pref.get("value", False))
                checkbox.connect("toggled", self._on_setting_change)
                self.pref_widgets[pref_id] = checkbox
                pref_box.pack_start(checkbox, False, False, 0)
            else:
                label = styled(Gtk.Label(label=pref_name, halign=Gtk.Align.START), "body")
                pref_box.pack_start(label, False, False, 0)

                if descr := pref.description:
                    desc_label = styled(
                        Gtk.Label(
                            label=ext_utils.autofmt_pango_code_block(descr),
                            halign=Gtk.Align.START,
                            wrap=True,
                            use_markup=True,
                        ),
                        "caption",
                        "dim-label",
                    )
                    pref_box.pack_start(desc_label, False, False, 0)

                widget = self._create_preference_widget(pref_id, pref, pref_type)
                if widget:
                    pref_box.pack_start(widget, False, False, 0)

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
            spin.connect("value-changed", self._on_setting_change)
            self.pref_widgets[pref_id] = spin
            return spin
        if pref_type == "select":
            return self._create_select_widget(pref_id, pref)
        if pref_type == "text":
            return self._create_text_widget(pref_id, pref)
        if pref_type == "input":
            entry = Gtk.Entry(text=str(pref.get("value", "")))
            entry.connect("changed", self._on_setting_change)
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
        combo.connect("changed", self._on_setting_change)
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
        textview.get_buffer().connect("changed", self._on_setting_change)
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

    def _on_setting_change(self, _widget: Gtk.Widget) -> None:
        if self.save_button:
            self.save_button.set_sensitive(True)

    def _on_add_extension(self, _widget: Gtk.Widget) -> None:
        def after_add_extension(ext: ExtensionController) -> None:
            self.active_ext = ext
            self._load_extension_list()
            self._show_extension_details(ext)

        self.layout.select_item(None)
        self.handlers.add_extension(after_add_extension)

    def _on_toggle_extension(self, _switch: Gtk.Switch, state: bool, ext: ExtensionController) -> None:
        self.handlers.toggle_extension(state, ext)

    def _on_check_updates(self, button: Gtk.Button, ext: ExtensionController) -> None:
        stop_spinner_button_animation = start_spinner_button_animation(button)

        self.handlers.check_updates(ext, stop_spinner_button_animation)

    def on_remove_extension(self, _button: Gtk.Button, ext: ExtensionController) -> None:
        def after_remove_extension() -> None:
            self.active_ext = None
            self._load_extension_list()
            self._show_placeholder()

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

        except (AttributeError, TypeError, ValueError):
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
