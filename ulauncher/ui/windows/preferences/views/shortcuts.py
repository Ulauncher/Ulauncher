from __future__ import annotations

import uuid
from time import time
from typing import cast

from gi.repository import Gtk, Pango

from ulauncher.modes.shortcuts.shortcuts_db import Shortcut, ShortcutsDb
from ulauncher.ui.windows.preferences import views
from ulauncher.ui.windows.preferences.utils.ext_utils import fmt_pango_code_block
from ulauncher.ui.windows.preferences.utils.sidebar_layout import SidebarItem, SidebarLayout
from ulauncher.ui.windows.preferences.views import (
    DialogLauncher,
    TextArea,
    get_window_for_widget,
    styled,
)
from ulauncher.utils.load_icon_surface import load_icon_surface


class ShortcutsView(views.BaseView):
    active_shortcut_id: str | None = None
    shortcuts: dict[str, Shortcut] = {}
    save_button: Gtk.Button | None = None
    """Shortcuts management page"""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, hexpand=True, halign=Gtk.Align.FILL)

        self.layout = SidebarLayout(
            footer_actions=[("Add Shortcut", "list-add-symbolic", self._on_add_shortcut)],
        )
        self.pack_start(self.layout, True, True, 0)

        self._load_shortcut_list()
        self._show_placeholder()

    def _create_edit_form(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the edit form with shortcut data"""
        form_box = self._create_form_container()
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20, hexpand=True)
        content_box.pack_start(self._create_icon_button_row(shortcut), False, False, 0)
        content_box.pack_start(self._create_name_keyword_row(shortcut), False, False, 0)
        content_box.pack_start(self._create_command_section(shortcut), True, True, 0)
        content_box.pack_start(self._create_options_section(shortcut), False, False, 0)
        form_box.pack_start(content_box, True, True, 0)

        self.selected_icon_path = shortcut.icon or ""
        self._update_icon_button()

        return form_box

    def _create_form_container(self) -> Gtk.Box:
        """Create the main form container"""
        return styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin=20), "edit-form")

    def _create_icon_button_row(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the top row with icon on left and action buttons on right"""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        # Icon section on the left
        icon_section = self._create_icon_section()
        row.pack_start(icon_section, False, False, 0)

        # Buttons on the right
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, valign=Gtk.Align.CENTER)

        remove_button = styled(
            Gtk.Button(label="Remove", sensitive=bool(shortcut.id)), "shortcuts-button", "destructive-action"
        )
        remove_button.connect("clicked", self._on_remove_current)

        save_button = styled(Gtk.Button(label="Save", sensitive=False), "shortcuts-button", "suggested-action")
        save_button.connect("clicked", self._on_save_shortcut)
        self.save_button = save_button

        button_box.pack_start(save_button, False, False, 0)
        button_box.pack_start(remove_button, False, False, 0)

        row.pack_end(button_box, False, False, 0)

        return row

    def _create_name_keyword_row(self, shortcut: Shortcut) -> Gtk.Box:
        """Create the row with name and keyword fields"""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        # Name section
        name_section = self._create_name_section(shortcut)
        row.pack_start(name_section, True, True, 0)

        # Keyword section
        keyword_section = self._create_keyword_section(shortcut)
        row.pack_start(keyword_section, True, True, 0)

        return row

    def _create_icon_section(self) -> Gtk.Box:
        """Create the icon selection section"""
        icon_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, valign=Gtk.Align.CENTER)

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

        cmd_help_expander = styled(Gtk.Expander(label="Show help and examples"), "shortcuts-cmd-help")
        cmd_script_codeblock = '#!/bin/bash\nnotify-send "Notification" "$*"'
        cmd_examples_label = Gtk.Label(
            label=(
                f"Use {fmt_pango_code_block('%s')} as the argument placeholder. "
                f"For scripts you can also use: {fmt_pango_code_block('$*')} or {fmt_pango_code_block('$@')}.\n\n"
                "<b>URL shortcut example</b> (google search)\n"
                f"{fmt_pango_code_block('https://www.google.com/search?q=%s')}\n\n"
                "<b>Script shortcut example</b> (send notification)\n"
                f"{fmt_pango_code_block(cmd_script_codeblock)}\n\n"
                f"*1 Note that scripts must start with a shebang ({fmt_pango_code_block('#!')})\n"
                f"*2 Run {fmt_pango_code_block('ulauncher --verbose')} to see any output from scripts"
            ),
            use_markup=True,
            halign=Gtk.Align.START,
            wrap=True,
            selectable=True,
        )

        cmd_help_expander.add(cmd_examples_label)
        cmd_section.pack_start(cmd_help_expander, False, False, 5)

        scrolled_cmd = styled(
            Gtk.ScrolledWindow(min_content_height=100, shadow_type=Gtk.ShadowType.IN),
            "shortcuts-command-editor",
        )

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
        row = styled(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, spacing=12), "shortcuts-option-row")

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)

        title_label = styled(Gtk.Label(label=title, halign=Gtk.Align.START), "preferences-setting-title")
        description_label = styled(
            Gtk.Label(label=description, halign=Gtk.Align.START, wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR),
            "preferences-setting-description",
        )

        text_box.pack_start(title_label, False, False, 0)
        text_box.pack_start(description_label, False, False, 0)
        row.pack_start(text_box, True, True, 0)

        option_switch = Gtk.Switch(active=active, halign=Gtk.Align.END, valign=Gtk.Align.CENTER)
        row.pack_end(option_switch, False, False, 0)

        option_switch.connect("notify::active", lambda switch, _pspec: self._on_form_field_changed(switch))

        container.pack_start(row, False, False, 0)
        return option_switch

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
        """Load shortcuts from database and populate sidebar"""
        # Load shortcuts data
        self.shortcuts = cast("dict[str, Shortcut]", ShortcutsDb.load())

        # Convert shortcuts to SidebarItems
        items: list[SidebarItem] = []
        for shortcut_id, shortcut in self.shortcuts.items():
            if shortcut:  # Skip None values (deleted shortcuts)
                icon_surface = load_icon_surface(shortcut.icon, views.ICON_SIZE_M, self.get_scale_factor())
                icon_image = Gtk.Image.new_from_surface(icon_surface)

                item = SidebarItem(
                    id=shortcut_id,
                    icon=icon_image,
                    name=shortcut.name or "Unnamed",
                    description=shortcut.keyword,
                    on_activate=self._on_shortcut_item_activated,
                )
                items.append(item)

        self.layout.set_items(items, self.active_shortcut_id)

    def _on_shortcut_item_activated(self, item: SidebarItem) -> None:
        """Handle shortcut selection in sidebar"""
        shortcut = self.shortcuts.get(item.id)
        if shortcut:
            self.active_shortcut_id = item.id
            self._show_edit_form(shortcut)
        else:
            self.active_shortcut_id = None
            self._show_placeholder()

    def _on_add_shortcut(self, _widget: Gtk.Widget) -> None:
        """Handle add shortcut button click"""
        self.active_shortcut_id = None
        self.layout.select_item(None)
        self._show_edit_form(Shortcut())

    def _on_remove_current(self, _button: Gtk.Button) -> None:
        """Handle remove current shortcut button click"""
        if not self.active_shortcut_id:
            return

        shortcut = self.shortcuts.get(self.active_shortcut_id)
        if not shortcut:
            return

        response = DialogLauncher(self).show_question(
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

        placeholder_box.pack_start(heading_label, False, False, 0)
        placeholder_box.pack_start(hint_label, False, False, 0)

        self.layout.set_content(placeholder_box)

    def _show_edit_form(self, shortcut: Shortcut) -> None:
        """Show shortcut editing form"""
        form_container = self._create_edit_form(shortcut)
        self.layout.set_content(form_container)

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
        icon_surface = load_icon_surface(self.selected_icon_path, views.ICON_SIZE_L, self.get_scale_factor())
        icon = Gtk.Image.new_from_surface(icon_surface)
        self.icon_button.set_image(icon)

    def _on_select_icon(self, _button: Gtk.Button) -> None:
        """Handle icon selection"""
        dialog = Gtk.FileChooserDialog(
            title="Select Icon", transient_for=get_window_for_widget(self), action=Gtk.FileChooserAction.OPEN
        )
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
