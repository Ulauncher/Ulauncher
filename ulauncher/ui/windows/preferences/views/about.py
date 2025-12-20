from __future__ import annotations

from gi.repository import Gtk

from ulauncher import api_version, paths, version
from ulauncher.ui.windows.preferences.views import BaseView, styled
from ulauncher.utils.launch_detached import open_detached
from ulauncher.utils.load_icon_surface import load_icon_surface

ABOUT_VIEW_LOGO_SIZE = 200


class AboutView(BaseView):
    """About page with application information"""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, margin=40, spacing=30)

        # Left column - Logo and version info
        left_column = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, hexpand=True, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER
        )
        surface = load_icon_surface(
            f"{paths.ASSETS}/icons/system/apps/ulauncher.svg", ABOUT_VIEW_LOGO_SIZE, self.get_scale_factor()
        )
        logo_image = Gtk.Image.new_from_surface(surface)
        left_column.pack_start(logo_image, False, False, 0)

        version_label = styled(Gtk.Label(label=f"Version {version}", halign=Gtk.Align.CENTER, margin_top=15), "title-4")
        left_column.pack_start(version_label, False, False, 0)

        api_label = styled(
            Gtk.Label(label=f"Extension API: v{api_version}", halign=Gtk.Align.CENTER, margin_top=5), "dim-label"
        )
        left_column.pack_start(api_label, False, False, 0)

        self.pack_start(left_column, True, True, 0)

        # Right column - Application information
        right_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, hexpand=True, valign=Gtk.Align.CENTER)

        name_label = styled(Gtk.Label(label="Ulauncher", halign=Gtk.Align.START), "title-1")
        right_column.pack_start(name_label, False, False, 0)

        desc_label = Gtk.Label(
            label="Ulauncher is a fast, feature-rich and extensible application launcher",
            halign=Gtk.Align.START,
        )
        right_column.pack_start(desc_label, False, False, 0)

        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.START, spacing=10)

        website_button = Gtk.Button(label="Website")
        website_button.connect("clicked", lambda _: open_detached("https://ulauncher.io"))
        buttons_box.pack_start(website_button, False, False, 0)

        github_button = Gtk.Button(label="GitHub")
        github_button.connect("clicked", lambda _: open_detached("https://github.com/Ulauncher/Ulauncher"))
        buttons_box.pack_start(github_button, False, False, 0)

        right_column.pack_start(buttons_box, False, False, 0)

        # Copyright and license
        copyright_label = styled(
            Gtk.Label(
                label="© 2014-2025 Ulauncher Contributors\nLicensed under GNU General Public License v3.0",
                halign=Gtk.Align.START,
                justify=Gtk.Justification.LEFT,
                margin_top=30,
            ),
            "dim-label",
        )
        right_column.pack_start(copyright_label, False, False, 0)

        self.pack_start(right_column, True, True, 0)
