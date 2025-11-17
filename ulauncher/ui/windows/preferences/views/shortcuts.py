from __future__ import annotations

import uuid
from time import time
from typing import cast

from gi.repository import Gtk, Pango

from ulauncher.modes.shortcuts.shortcuts_db import Shortcut, ShortcutsDb
from ulauncher.ui.windows.preferences import views
from ulauncher.ui.windows.preferences.views import DataListBoxRow, TextArea, styled
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
                spacing=10,
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

        self.pack_start(left_sidebar, False, False, 0)

        # Right side - details view
        self.details_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, halign=Gtk.Align.FILL)
        self.pack_start(self.details_view, True, True, 0)

        self._load_shortcut_list()
        self._show_placeholder()

    def _create_edit_form(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the edit form with shortcut data"""
        form_box = self._create_form_container()
        form_box.pack_start(self._create_form_header(shortcut), False, False, 0)
        form_box.pack_start(self._create_icon_name_keyword_row(shortcut), False, False, 0)
        form_box.pack_start(self._create_command_section(shortcut), True, True, 0)
        form_box.pack_start(self._create_options_section(shortcut), False, False, 0)

        self.selected_icon_path = shortcut.icon
        self._update_icon_button()

        return form_box

    def _create_form_container(self) -> Gtk.Box:
        """Create the main form container"""
        return styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin=20), "edit-form")

    def _create_form_header(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the form header with title and toolbar buttons"""
        form_title = "Edit shortcut" if shortcut.id else "Add shortcut"
        header_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.form_title = styled(Gtk.Label(label=form_title, halign=Gtk.Align.START), "title-2")
        header_toolbar.pack_start(self.form_title, True, True, 0)

        toolbar_buttons = [
            ("Save", "checkmark-symbolic", self._on_save_shortcut, False, []),
            ("Remove", "user-trash-symbolic", self._on_delete_current, bool(shortcut.id), ["destructive-action"]),
            ("Close", "window-close-symbolic", self._on_close_edit_form, bool(shortcut.id), []),
        ]

        for label, icon_name, callback, sensitive, class_names in toolbar_buttons:
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            button = styled(Gtk.Button(image=icon, tooltip_text=label, sensitive=sensitive), *class_names)
            button.connect("clicked", callback)
            header_toolbar.pack_start(button, False, False, 0)
            if label == "Save":
                self.save_button = button

        return header_toolbar

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
        icon_label = Gtk.Label(label="Icon", halign=Gtk.Align.START)
        icon_section.pack_start(icon_label, False, False, 0)

        self.icon_button = Gtk.Button(width_request=views.ICON_SIZE_L, height_request=views.ICON_SIZE_L)
        self.icon_button.connect("clicked", self._on_select_icon)
        icon_section.pack_start(self.icon_button, False, False, 0)

        return icon_section

    def _create_name_section(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the name input section"""
        name_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        name_label = Gtk.Label(label="Name", halign=Gtk.Align.START)
        name_section.pack_start(name_label, False, False, 0)

        self.name_entry = Gtk.Entry(text=shortcut.name, placeholder_text="Enter shortcut name")
        self.name_entry.connect("changed", self._on_form_field_changed)
        name_section.pack_start(self.name_entry, False, False, 0)

        return name_section

    def _create_keyword_section(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the keyword input section"""
        keyword_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        keyword_label = Gtk.Label(label="Keyword", halign=Gtk.Align.START)
        keyword_section.pack_start(keyword_label, False, False, 0)

        self.keyword_entry = Gtk.Entry(text=shortcut.keyword, placeholder_text="Enter keyword")
        self.keyword_entry.connect("changed", self._on_form_field_changed)
        keyword_section.pack_start(self.keyword_entry, False, False, 0)

        return keyword_section

    def _create_command_section(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the command/script input section"""
        cmd_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        cmd_label = Gtk.Label(label="Query or script", halign=Gtk.Align.START)
        cmd_section.pack_start(cmd_label, False, False, 0)

        scrolled_cmd = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, min_content_height=100)

        self.cmd_textview = TextArea(monospace=True, top_margin=10, bottom_margin=10, left_margin=10, right_margin=10)
        self.cmd_textview.set_text(shortcut.cmd)
        self.cmd_textview.get_buffer().connect("changed", self._on_form_field_changed)
        scrolled_cmd.add(self.cmd_textview)

        cmd_section.pack_start(scrolled_cmd, True, True, 0)

        return cmd_section

    def _create_options_section(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the options checkboxes section"""
        options_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)

        self.run_without_argument_check = Gtk.CheckButton(
            label="Static shortcut (doesn't take arguments)", active=shortcut.run_without_argument
        )
        self.run_without_argument_check.connect("toggled", self._on_form_field_changed)
        options_row.pack_start(self.run_without_argument_check, False, False, 0)

        self.is_default_search_check = Gtk.CheckButton(
            label="Include in fallback for search results", active=shortcut.is_default_search
        )
        self.is_default_search_check.connect("toggled", self._on_form_field_changed)
        options_row.pack_start(self.is_default_search_check, False, False, 0)

        return options_row

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
        style = self.save_button.get_style_context()

        if is_valid:
            style.add_class("suggested-action")
        else:
            style.remove_class("suggested-action")

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

        if not self.shortcuts:
            # Show empty state
            empty_label = styled(
                Gtk.Label(label="No shortcuts configured", margin_top=50, margin_bottom=50), "caption", "dim-label"
            )
            empty_row = Gtk.ListBoxRow(selectable=False, activatable=False)
            empty_row.add(empty_label)
            shortcuts_listbox.add(empty_row)

        # Clear existing listbox
        for child in self.listbox_container.get_children():
            self.listbox_container.remove(child)

        # Add listbox to container
        self.listbox_container.pack_start(shortcuts_listbox, True, True, 0)
        shortcuts_listbox.show_all()

        # Connect signal (must happen after setting the initial selection)
        shortcuts_listbox.connect("row-selected", self._on_shortcut_selected)

    def _create_shortcut_row(self, shortcut_id: str, shortcut: Shortcut) -> DataListBoxRow:
        """Create a shortcut row for the list"""
        row = DataListBoxRow(shortcut_id)

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin=8)

        # Icon
        icon_image: Gtk.Image | None = None
        icon_path = shortcut.icon
        icon_surface = load_icon_surface(icon_path, views.ICON_SIZE_S, self.get_scale_factor())
        icon_image = Gtk.Image.new_from_surface(icon_surface)

        main_box.pack_start(icon_image, False, False, 0)

        # Info box
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)

        # Name
        name_label = styled(
            Gtk.Label(label=shortcut.name or "Unnamed", ellipsize=Pango.EllipsizeMode.END, halign=Gtk.Align.START),
            "body",
        )
        info_box.pack_start(name_label, False, False, 0)

        # Keyword
        keyword_label = styled(
            Gtk.Label(label=shortcut.keyword, ellipsize=Pango.EllipsizeMode.END, halign=Gtk.Align.START),
            "caption",
            "dim-label",
        )
        info_box.pack_start(keyword_label, False, False, 0)

        main_box.pack_start(info_box, True, True, 0)

        row.add(main_box)
        return row

    def _on_add_shortcut(self, _button: Gtk.Button) -> None:
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

    def _on_delete_current(self, _button: Gtk.Button) -> None:
        """Handle delete current shortcut button click"""
        if not self.active_shortcut_id:
            return

        shortcut = self.shortcuts.get(self.active_shortcut_id)
        if not shortcut:
            return

        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f'Delete shortcut "{shortcut.name}"?',
            secondary_text="This action cannot be undone.",
        )

        response = dialog.run()
        dialog.destroy()

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

        # Create placeholder
        placeholder_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER, spacing=10
        )

        # First row with "Add shortcut" text and button
        add_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, halign=Gtk.Align.CENTER)

        add_shortcut_label = styled(Gtk.Label(label="Add shortcut"), "title-3", "dim-label")
        add_row.pack_start(add_shortcut_label, False, False, 0)

        add_button = Gtk.Button(label="+", width_request=30, height_request=30, tooltip_text="Add Shortcut")
        add_button.connect("clicked", self._on_add_shortcut)
        add_row.pack_start(add_button, False, False, 0)

        placeholder_box.pack_start(add_row, False, False, 0)

        # Second row with "or select a shortcut to edit"
        select_label = Gtk.Label(label="or select a shortcut to edit", halign=Gtk.Align.CENTER)
        styled(select_label, "body", "dim-label")

        placeholder_box.pack_start(select_label, False, False, 0)

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
        save_button.get_style_context().remove_class("suggested-action")
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
        filter_images.add_mime_type("image/*")
        dialog.add_filter(filter_images)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_icon_path = dialog.get_filename() or ""
            self._update_icon_button()
            self._on_form_field_changed(self.icon_button)

        dialog.destroy()

    def _on_close_edit_form(self, _button: Gtk.Button) -> None:
        """Handle close button click to return to placeholder"""
        # Reset state and reload
        self.active_shortcut_id = None
        self._load_shortcut_list()  # Reload without selection
        self._show_placeholder()
