from __future__ import annotations

import uuid
from time import time
from typing import cast

from gi.repository import Gtk, Pango

from ulauncher.modes.shortcuts.shortcuts_db import Shortcut, ShortcutsDb
from ulauncher.ui.windows.preferences import views
from ulauncher.ui.windows.preferences.views import DataListBoxRow, DialogLauncher, TextArea, styled
from ulauncher.utils.load_icon_surface import load_icon_surface


class ShortcutsView(views.BaseView):
    active_shortcut_id: str | None = None
    shortcuts: dict[str, Shortcut] = {}
    save_button: Gtk.Button | None = None
    """Shortcuts management page"""

    def __init__(self, window: Gtk.Window) -> None:
        super().__init__(window, orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, halign=Gtk.Align.FILL)

        left_sidebar = styled(
            Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                hexpand=False,
                halign=Gtk.Align.START,
                width_request=views.SIDEBAR_WIDTH,
            ),
            "sidebar",
        )

        # Scrolled window for shortcuts list
        scrolled = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.listbox_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scrolled.add(self.listbox_container)

        left_sidebar.pack_start(scrolled, True, True, 0)

        divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        left_sidebar.pack_start(divider, False, False, 0)

        actions_listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        actions_listbox.set_activate_on_single_click(True)
        actions_listbox.connect("row-activated", self._on_actions_row_activated)
        actions_listbox.add(self._create_add_shortcut_row())
        actions_listbox.show_all()
        left_sidebar.pack_start(actions_listbox, False, False, 0)

        self.pack_start(left_sidebar, False, False, 0)

        # Vertical separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(separator, False, False, 0)

        # Right side - details view
        self.details_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, halign=Gtk.Align.FILL)
        self.pack_start(self.details_view, True, True, 0)

        self._load_shortcut_list()
        self._show_placeholder()

    def _create_edit_form(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the edit form with shortcut data"""
        form_box = self._create_form_container()
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20, hexpand=True)
        content_box.pack_start(self._create_icon_name_keyword_row(shortcut), False, False, 0)
        content_box.pack_start(self._create_command_section(shortcut), True, True, 0)
        content_box.pack_start(self._create_options_section(shortcut), False, False, 0)
        form_box.pack_start(content_box, True, True, 0)
        form_box.pack_start(self._create_button_row(shortcut), False, True, 0)

        self.selected_icon_path = shortcut.icon or ""
        self._update_icon_button()
        self._on_form_field_changed(self.name_entry)

        return form_box

    def _create_form_container(self) -> Gtk.Box:
        """Create the main form container"""
        return styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin=20), "edit-form")

    def _create_icon_name_keyword_row(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the top row with icon, name, and keyword fields"""
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        # Icon section
        icon_section = self._create_icon_section()
        top_row.pack_start(icon_section, False, False, 0)

        # Name section
        name_section = self._create_name_section(shortcut)
        top_row.pack_start(name_section, True, True, 0)

        # Keyword section
        keyword_section = self._create_keyword_section(shortcut)
        top_row.pack_start(keyword_section, True, True, 0)

        return top_row

    def _create_icon_section(self) -> Gtk.Box:
        """Create the icon selection section"""
        icon_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        icon_section.set_margin_top(6)

        self.icon_button = Gtk.Button(width_request=views.ICON_SIZE_L, height_request=views.ICON_SIZE_L)
        self.icon_button.connect("clicked", self._on_select_icon)
        icon_section.pack_start(self.icon_button, False, False, 0)

        return icon_section

    def _create_name_section(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the name input section"""
        name_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        name_label = Gtk.Label(label="Name", halign=Gtk.Align.START)
        name_section.pack_start(name_label, False, False, 0)

        self.name_entry = styled(
            Gtk.Entry(text=shortcut.name, placeholder_text="Enter shortcut name"),
            "shortcuts-entry",
        )
        self.name_entry.connect("changed", self._on_form_field_changed)
        name_section.pack_start(self.name_entry, False, False, 0)

        return name_section

    def _create_keyword_section(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the keyword input section"""
        keyword_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        keyword_label = Gtk.Label(label="Keyword", halign=Gtk.Align.START)
        keyword_section.pack_start(keyword_label, False, False, 0)

        self.keyword_entry = styled(
            Gtk.Entry(text=shortcut.keyword, placeholder_text="Enter keyword"),
            "shortcuts-entry",
        )
        self.keyword_entry.connect("changed", self._on_form_field_changed)
        keyword_section.pack_start(self.keyword_entry, False, False, 0)

        return keyword_section

    def _create_command_section(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the command/script input section"""
        cmd_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        cmd_label = Gtk.Label(label="Query or script", halign=Gtk.Align.START)
        cmd_section.pack_start(cmd_label, False, False, 0)

        scrolled_cmd = styled(
            Gtk.ScrolledWindow(min_content_height=100),
            "shortcuts-command-editor",
        )
        scrolled_cmd.set_shadow_type(Gtk.ShadowType.IN)

        self.cmd_textview = TextArea(monospace=True, top_margin=10, bottom_margin=10, left_margin=10, right_margin=10)
        self.cmd_textview.set_text(shortcut.cmd)
        self.cmd_textview.get_buffer().connect("changed", self._on_form_field_changed)
        scrolled_cmd.add(self.cmd_textview)

        cmd_section.pack_start(scrolled_cmd, True, True, 0)

        return cmd_section

    def _create_options_section(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the options switches section"""
        options_box = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0), "shortcuts-options")

        self.run_without_argument_check = self._add_option_row(
            options_box,
            title="Static shortcut",
            description="Run this shortcut without passing additional text typed by the user.",
            active=shortcut.run_without_argument,
        )

        self.is_default_search_check = self._add_option_row(
            options_box,
            title="Use as fallback result",
            description="Show this shortcut automatically when no other search results are available.",
            active=shortcut.is_default_search,
        )

        return options_box

    def _add_option_row(self, container: Gtk.Box, title: str, description: str, active: bool) -> Gtk.Switch:
        row = styled(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12), "shortcuts-option-row")
        row.set_hexpand(True)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)

        title_label = styled(Gtk.Label(label=title, halign=Gtk.Align.START), "preferences-setting-title")
        description_label = styled(
            Gtk.Label(label=description, halign=Gtk.Align.START, wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR),
            "preferences-setting-description",
        )
        description_label.set_line_wrap(True)

        text_box.pack_start(title_label, False, False, 0)
        text_box.pack_start(description_label, False, False, 0)
        row.pack_start(text_box, True, True, 0)

        option_switch = Gtk.Switch(active=active)
        option_switch.set_halign(Gtk.Align.END)
        option_switch.set_valign(Gtk.Align.CENTER)
        row.pack_end(option_switch, False, False, 0)

        option_switch.connect("notify::active", lambda switch, _pspec: self._on_form_field_changed(switch))

        container.pack_start(row, False, False, 0)
        return option_switch

    def _create_button_row(self, shortcut: Shortcut) -> Gtk.Box:
        button_row = styled(
            Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, hexpand=True),
            "shortcuts-button-row",
        )
        spacer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_row.pack_start(spacer, True, True, 0)

        remove_button = styled(Gtk.Button(label="Remove"), "shortcuts-button", "destructive-action")
        remove_button.set_sensitive(bool(shortcut.id))
        remove_button.connect("clicked", self._on_remove_current)

        save_button = styled(Gtk.Button(label="Save"), "shortcuts-button", "suggested-action")
        save_button.set_sensitive(False)
        save_button.connect("clicked", self._on_save_shortcut)
        self.save_button = save_button

        for button in [remove_button, save_button]:
            button_row.pack_start(button, False, False, 0)

        return button_row

    def _on_form_field_changed(self, _widget: Gtk.Widget) -> None:
        """Handle form field changes and validate form"""
        if not self.save_button:
            return

        # Get form values
        name = self.name_entry.get_text().strip()
        keyword = self.keyword_entry.get_text().strip()
        cmd = self.cmd_textview.get_text().strip()

        # Validate form
        is_valid = bool(name and keyword and cmd)
        tooltip = "Save" if is_valid else "Please fill all fields"
        self.save_button.set_sensitive(is_valid)
        self.save_button.set_tooltip_text(tooltip)

    def _load_shortcut_list(self) -> None:
        """Load shortcuts from database and recreate listbox"""
        # Create new listbox
        shortcuts_listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)

        # Load shortcuts data
        self.shortcuts = cast("dict[str, Shortcut]", ShortcutsDb.load())

        # Add shortcut rows
        for shortcut_id, shortcut in self.shortcuts.items():
            if shortcut:  # Skip None values (deleted shortcuts)
                row = self._create_shortcut_row(shortcut_id, shortcut)
                shortcuts_listbox.add(row)

                # Track row for selection if it matches active_shortcut_id
                if shortcut_id == self.active_shortcut_id:
                    shortcuts_listbox.select_row(row)

        # Clear existing listbox
        for child in self.listbox_container.get_children():
            self.listbox_container.remove(child)

        # Add listbox to container
        self.listbox_container.pack_start(shortcuts_listbox, True, True, 0)
        shortcuts_listbox.show_all()

        # Connect signal (must happen after setting the initial selection)
        shortcuts_listbox.connect("row-selected", self._on_shortcut_selected)

    def _create_add_shortcut_row(self) -> Gtk.ListBoxRow:
        """Create the persistent Add Shortcut action row"""
        row = DataListBoxRow("add-shortcut")
        row.set_selectable(False)
        row.set_can_focus(True)
        row.set_activatable(True)
        row.set_tooltip_text("Create a new shortcut")

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_box.set_margin_top(4)
        action_box.set_margin_bottom(4)
        action_box.set_margin_start(8)
        action_box.set_margin_end(8)

        icon = Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.MENU)
        icon.set_pixel_size(18)
        action_box.pack_start(icon, False, False, 0)

        label = styled(
            Gtk.Label(label="Add Shortcut", halign=Gtk.Align.START),
            "sidebar-item-name",
        )
        action_box.pack_start(label, True, True, 0)

        row.add(action_box)
        row.set_margin_bottom(8)
        row.set_margin_top(8)
        return row

    def _create_shortcut_row(self, shortcut_id: str, shortcut: Shortcut) -> DataListBoxRow:
        """Create a shortcut row for the list"""
        row = DataListBoxRow(shortcut_id)

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin=6)

        # Icon
        icon_image: Gtk.Image | None = None
        icon_path = shortcut.icon
        icon_surface = load_icon_surface(icon_path, views.ICON_SIZE_M, self.get_scale_factor())
        icon_image = Gtk.Image.new_from_surface(icon_surface)

        main_box.pack_start(icon_image, False, False, 0)

        # Info box
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1, hexpand=True)

        # Name
        name_label = styled(
            Gtk.Label(label=shortcut.name or "Unnamed", ellipsize=Pango.EllipsizeMode.END, halign=Gtk.Align.START),
            "sidebar-item-name",
        )
        info_box.pack_start(name_label, False, False, 0)

        # Keyword
        keyword_label = styled(
            Gtk.Label(label=shortcut.keyword, ellipsize=Pango.EllipsizeMode.END, halign=Gtk.Align.START),
            "dim-label",
            "sidebar-item-description",
        )
        info_box.pack_start(keyword_label, False, False, 0)

        main_box.pack_start(info_box, True, True, 0)

        row.add(main_box)
        return row

    def _on_actions_row_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        """Handle action rows activated in the sidebar"""
        if isinstance(row, DataListBoxRow) and row.id == "add-shortcut":
            self._on_add_shortcut()

    def _on_add_shortcut(self, _widget: Gtk.Widget | None = None) -> None:
        """Handle add shortcut button click"""
        self.active_shortcut_id = None
        self._show_edit_form(Shortcut())

    def _on_shortcut_selected(self, _listbox: Gtk.ListBox, row: DataListBoxRow | None) -> None:
        """Handle shortcut selection in sidebar"""
        if not row:
            self.active_shortcut_id = None
            self._show_placeholder()
            return

        shortcut = self.shortcuts.get(row.id)
        if shortcut:
            self.active_shortcut_id = row.id
            self._show_edit_form(shortcut)
        else:
            self.active_shortcut_id = None
            self._show_placeholder()

    def _on_remove_current(self, _button: Gtk.Button) -> None:
        """Handle remove current shortcut button click"""
        if not self.active_shortcut_id:
            return

        shortcut = self.shortcuts.get(self.active_shortcut_id)
        if not shortcut:
            return

        response = DialogLauncher(self.window).show_question(
            f'Remove shortcut "{shortcut.name}"?', "This action cannot be undone."
        )
        if response == Gtk.ResponseType.YES:
            # Remove from database
            shortcuts_db = ShortcutsDb.load()
            shortcuts_db.save({self.active_shortcut_id: None})
            self.active_shortcut_id = None
            self._load_shortcut_list()
            # Show placeholder after deletion
            self._show_placeholder()

    def _show_placeholder(self) -> None:
        """Show placeholder when no shortcut is selected"""
        # Clear existing content
        for child in self.details_view.get_children():
            self.details_view.remove(child)

        has_shortcuts = any(self.shortcuts.values())
        heading = "Select a shortcut to edit" if has_shortcuts else "Create your first shortcut"
        hint = (
            "Choose a shortcut from the list or create a new one from the sidebar."
            if has_shortcuts
            else "Click the Add Shortcut button in the sidebar to create a new shortcut."
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
        hint_label.set_line_wrap(True)

        placeholder_box.pack_start(heading_label, False, False, 0)
        placeholder_box.pack_start(hint_label, False, False, 0)

        self.details_view.pack_start(placeholder_box, True, True, 0)
        self.details_view.show_all()

    def _show_edit_form(self, shortcut: Shortcut) -> None:
        """Show shortcut editing form"""
        # Clear existing content
        for child in self.details_view.get_children():
            self.details_view.remove(child)

        # Create edit form
        form_container = self._create_edit_form(shortcut)
        self.details_view.pack_start(form_container, True, True, 0)
        self.details_view.show_all()

    def _on_save_shortcut(self, save_button: Gtk.Button) -> None:
        if not save_button.get_sensitive():
            return

        # Save shortcut
        shortcut_id = self.active_shortcut_id or str(uuid.uuid4())
        existing_shortcut = self.shortcuts.get(shortcut_id, Shortcut())

        shortcut = Shortcut(
            id=shortcut_id,
            name=self.name_entry.get_text().strip(),
            keyword=self.keyword_entry.get_text().strip(),
            cmd=self.cmd_textview.get_text().strip(),
            icon=self.selected_icon_path,
            is_default_search=self.is_default_search_check.get_active(),
            run_without_argument=self.run_without_argument_check.get_active(),
            added=existing_shortcut.get("added", int(time())),
        )

        shortcuts_db = ShortcutsDb.load()
        shortcuts_db.save({shortcut_id: shortcut})

        # Disable save button after successful save
        save_button.set_sensitive(False)

        # Reload and maintain selection
        self.active_shortcut_id = shortcut_id
        self._load_shortcut_list()  # This will automatically select the active shortcut

    def save_changes(self) -> bool:
        """Public method to save current shortcut, returns True if save was attempted"""
        if self.save_button:
            self._on_save_shortcut(self.save_button)
            return True
        return False

    def _update_icon_button(self) -> None:
        """Update the icon button image"""
        icon: Gtk.Image | None = None
        icon_surface = load_icon_surface(self.selected_icon_path, views.ICON_SIZE_M, self.get_scale_factor())
        icon = Gtk.Image.new_from_surface(icon_surface)
        self.icon_button.set_image(icon)

    def _on_select_icon(self, _button: Gtk.Button) -> None:
        """Handle icon selection"""
        toplevel = self.get_toplevel()
        if not isinstance(toplevel, Gtk.Window):
            return

        dialog = Gtk.FileChooserDialog(title="Select Icon", parent=toplevel, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        # Add image filter
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Image files")
        filter_images.add_pixbuf_formats()
        dialog.add_filter(filter_images)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_icon_path = dialog.get_filename() or ""
            self._update_icon_button()
            self._on_form_field_changed(self.icon_button)

        dialog.destroy()
