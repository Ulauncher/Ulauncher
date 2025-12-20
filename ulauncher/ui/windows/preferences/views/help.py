from __future__ import annotations

from gi.repository import Gtk

from ulauncher.ui.windows.preferences.views import BaseView, styled
from ulauncher.utils.launch_detached import open_detached


class HelpView(BaseView):
    """Help page with useful information and links"""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        scrolled = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.pack_start(scrolled, True, True, 0)

        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=30, spacing=30)
        scrolled.add(main_container)

        # Two-column layout
        columns_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30, homogeneous=True)
        main_container.pack_start(columns_box, True, True, 0)

        # Left column - Links
        self._add_links_column(columns_box)

        # Right column - Keyboard shortcuts
        self._add_shortcuts_column(columns_box)

    def _add_links_column(self, parent: Gtk.Box) -> None:
        """Add useful links column"""
        links_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        parent.pack_start(links_column, True, True, 0)

        # Column title
        links_label = styled(Gtk.Label(label="Help & resources", halign=Gtk.Align.START), "title-3")
        links_column.pack_start(links_label, False, False, 0)

        # Links container with nice styling
        links_frame = styled(Gtk.Frame(), "view")
        links_column.pack_start(links_frame, False, False, 0)

        links_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=20, spacing=8)
        links_frame.add(links_container)

        links = [
            ("🌐 Ulauncher Website", "https://ulauncher.io", "The Ulauncher website"),
            ("🔧 GitHub Repository", "https://github.com/Ulauncher/Ulauncher", "View source code and contribute"),
            ("🐛 Report Issues", "https://github.com/Ulauncher/Ulauncher/issues", "Report bugs and request features"),
            (
                "🔍 Troubleshooting",
                "https://github.com/Ulauncher/Ulauncher/discussions/categories/troubleshooting",
                "Get help with common problems",
            ),
            (
                "💬 Community Discussion",
                "https://github.com/Ulauncher/Ulauncher/discussions",
                "Join the community discussions",
            ),
            ("📚 Documentation", "https://docs.ulauncher.io", "Documentation for extensions and themes"),
        ]

        for emoji_name, url, description in links:
            # Create a horizontal box for each link
            link_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

            # Link button with improved styling
            link_button = styled(Gtk.Button(label=emoji_name, halign=Gtk.Align.START, tooltip_text=url), "flat")
            link_button.connect("clicked", lambda _, u=url: open_detached(u))

            # Description label
            desc_label = styled(
                Gtk.Label(label=description, halign=Gtk.Align.START, hexpand=True), "caption", "dim-label"
            )
            link_box.pack_start(link_button, False, False, 0)
            link_box.pack_start(desc_label, True, True, 0)

            links_container.pack_start(link_box, False, False, 0)

    def _add_shortcuts_column(self, parent: Gtk.Box) -> None:
        """Add keyboard shortcuts column"""
        shortcuts_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        parent.pack_start(shortcuts_column, True, True, 0)
        # Column title
        shortcuts_label = styled(Gtk.Label(label="Keyboard Shortcuts", halign=Gtk.Align.START), "title-3")
        shortcuts_column.pack_start(shortcuts_label, False, False, 0)

        # Shortcuts container with nice styling
        shortcuts_frame = styled(Gtk.Frame(), "view")
        shortcuts_column.pack_start(shortcuts_frame, False, False, 0)

        shortcuts_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=20, spacing=15)
        shortcuts_frame.add(shortcuts_container)

        # Create individual sections for better organization
        sections = [
            (
                "Search",
                [
                    ("Type to search", "Applications and files"),
                    ("Use keywords", "Shortcuts and extensions"),
                    ("Ctrl+Backspace", "Clear input"),
                ],
            ),
            (
                "Navigation",
                [
                    ("↑/↓ or Ctrl+J/K", "Navigate results"),
                    ("Alt+Number/Letter", "Jump to result by position"),
                    ("Enter", "Launch selected item"),
                    ("Escape", "Close window"),
                ],
            ),
        ]

        for section_title, shortcuts in sections:
            # Section title
            section_label = styled(Gtk.Label(label=section_title, use_markup=True, halign=Gtk.Align.START), "heading")
            shortcuts_container.pack_start(section_label, False, False, 0)
            # Shortcuts in this section
            for shortcut, description in shortcuts:
                key_label = styled(Gtk.Label(label=shortcut, halign=Gtk.Align.START, width_request=150), "accent")
                desc_label = styled(Gtk.Label(label=description, halign=Gtk.Align.START, hexpand=True), "body")
                shortcut_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                shortcut_box.pack_start(key_label, False, False, 0)
                shortcut_box.pack_start(desc_label, True, True, 0)
                shortcuts_container.pack_start(shortcut_box, False, False, 0)

            # Add some spacing between sections
            spacer = Gtk.Box(height_request=8)
            shortcuts_container.pack_start(spacer, False, False, 0)
