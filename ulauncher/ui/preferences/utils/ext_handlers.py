from __future__ import annotations

import logging
from typing import Callable

from gi.repository import Gtk

from ulauncher import paths
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.modes.extensions.extension_record import ExtensionRecord
from ulauncher.modes.extensions.extension_service import ext_service
from ulauncher.ui.preferences.views import DialogLauncher, get_window_for_widget, styled

logger = logging.getLogger(__name__)


class ExtensionHandlers:
    """Handles extension operations like install, remove, toggle, update, etc.

    The service operations report back through callbacks on the GLib main loop, so the
    handlers update the dialogs directly in them. The main loop stays free during the
    network work (it runs in Gio subprocesses), which keeps the progress dialogs spinning."""

    def __init__(self, widget: Gtk.Widget) -> None:
        self.widget = widget
        self.dialog_launcher = DialogLauncher(self.widget)

    def _show_progress_dialog(self, title: str, message: str) -> Gtk.Dialog:
        """Create a progress dialog with a spinning icon"""
        dialog = styled(
            Gtk.Dialog(title=title, transient_for=get_window_for_widget(self.widget), modal=True, resizable=False),
            "progress-dialog",
        )
        dialog.set_default_size(400, 150)

        # Create content area
        content_area = dialog.get_content_area()
        content_box = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10), "progress-content")
        content_area.pack_start(content_box, True, True, 0)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_halign(Gtk.Align.CENTER)

        # Note: Spinners will respect /org/gnome/desktop/interface/enable-animations
        # So people who disabled animations in Gnome thinking it will only apply to the DE's
        # own animations will get static spinners :'(
        spinner = Gtk.Spinner(active=True)
        header_box.pack_start(spinner, False, False, 0)

        title_label = styled(Gtk.Label(label=title), "title-4")
        header_box.pack_start(title_label, False, False, 0)

        content_box.pack_start(header_box, False, False, 0)

        message_label = Gtk.Label(label=message, wrap=True, justify=Gtk.Justification.CENTER, halign=Gtk.Align.CENTER)
        content_box.pack_start(message_label, False, False, 0)

        dialog.show_all()
        return dialog

    def add_extension(self, callback: Callable[[ExtensionRecord], None]) -> None:
        """Handle add extension button click"""
        dialog = Gtk.Dialog(title="Add Extension", transient_for=get_window_for_widget(self.widget), modal=True)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Add", Gtk.ResponseType.OK)
        dialog.set_default_size(500, 150)

        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)
        content_area.set_margin_top(20)
        content_area.set_margin_bottom(20)

        label = Gtk.Label(label="Enter extension URL:", halign=Gtk.Align.START)
        content_area.pack_start(label, False, False, 0)

        entry = Gtk.Entry(placeholder_text="https://github.com/user/repo.git")
        content_area.pack_start(entry, False, False, 0)

        # Handle Enter key press as "submit"
        entry.connect("activate", lambda _entry: dialog.response(Gtk.ResponseType.OK))

        dialog.show_all()
        entry.grab_focus()

        response = dialog.run()
        url = entry.get_text().strip()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and url:
            self.install_extension(url, callback)

    def install_extension(self, url: str, callback: Callable[[ExtensionRecord], None]) -> None:
        """Install extension from URL"""
        progress_dialog = self._show_progress_dialog(
            "Installing extension...", "Please wait while the extension is being installed."
        )
        progress_dialog.show()

        def on_installed(ext: ExtensionRecord) -> None:
            # no explicit start: the service reconciles after the install job and starts the
            # extension (fresh installs are enabled by default)
            progress_dialog.destroy()
            callback(ext)

        def on_error(error: Exception) -> None:
            progress_dialog.destroy()
            self._show_extension_operation_error(error, url, "install")

        ext_service.install(url, on_installed, on_error)

    def toggle_extension(self, state: bool, ext: ExtensionRecord) -> None:
        """Handle extension enable/disable toggle"""
        ext_service.toggle_enabled(ext, state)

    def remove_extension(self, ext: ExtensionRecord, callback: Callable[[], None]) -> None:
        """Handle extension removal"""
        text = f'Remove extension "{ext.display_manifest.name}"?'
        secondary_text = "This action cannot be undone."
        response = self.dialog_launcher.show_question(text, secondary_text)

        if response == Gtk.ResponseType.YES:
            progress_dialog = self._show_progress_dialog(
                "Removing extension...", "Please wait while the extension is being removed."
            )
            progress_dialog.show()

            def on_removed() -> None:
                progress_dialog.destroy()
                callback()

            def on_error(error: Exception) -> None:
                progress_dialog.destroy()
                self._show_extension_operation_error(error, ext.state.url, "remove")

            ext_service.uninstall(ext, on_removed, on_error)

    def check_updates(self, ext: ExtensionRecord, callback: Callable[[], None]) -> None:
        """Handle checking for extension updates"""

        def on_checked(has_update: bool, commit_hash: str) -> None:
            if has_update:
                self._show_update_dialog(ext, commit_hash, callback)
            else:
                callback()
                self.dialog_launcher.show(
                    f"No updates available for {ext.display_manifest.name}", "The extension is up to date."
                )

        def on_error(error: Exception) -> None:
            callback()
            self.dialog_launcher.show_error("Failed to check for updates", f"Error: {error!s}")

        ext_service.check_update(ext, on_checked, on_error)

    def update_extension(self, ext: ExtensionRecord, callback: Callable[[], None]) -> None:
        """Update the extension"""
        # Create progress dialog with spinner
        progress_dialog = self._show_progress_dialog(
            "Updating extension...", "Please wait while the extension is being updated."
        )
        progress_dialog.show()

        def on_updated(updated: bool) -> None:
            callback()
            progress_dialog.destroy()
            if updated:
                self.dialog_launcher.show(
                    "Extension updated successfully", f"{ext.display_manifest.name} has been updated."
                )
            else:
                self.dialog_launcher.show(
                    f"No updates available for {ext.display_manifest.name}", "The extension is up to date."
                )

        def on_error(error: Exception) -> None:
            callback()
            progress_dialog.destroy()
            self._show_extension_operation_error(error, ext.issues_url or ext.website_url, "update")

        ext_service.update(ext, on_updated, on_error)

    def _show_update_dialog(self, ext: ExtensionRecord, commit_hash: str, callback: Callable[[], None]) -> None:
        """Show dialog when update is available"""
        text = f"Update available for '{ext.display_manifest.name}'"
        secondary_text = f"New version: {commit_hash[:7]}\n\nDo you want to update now?"
        response = self.dialog_launcher.show_question(text, secondary_text)
        if response == Gtk.ResponseType.YES:
            self.update_extension(ext, callback)
        else:
            callback()

    def _show_extension_operation_error(self, error: BaseException, url: str, operation: str = "install") -> None:
        """Show detailed error dialog for extension operation failures"""
        error_type = type(error).__name__
        error_message = str(error)

        # Determine primary and secondary text based on error type
        if isinstance(error, ext_exceptions.UrlError):
            primary_text = "Invalid Extension URL"
            secondary_text = (
                "The URL should be a HTTPS git repository link or a path to a local git repository.\n\n"
                "Examples:\n"
                "• https://github.com/user/repo.git\n"
                "• https://codeberg.org/user/repo.git"
            )
        elif isinstance(error, ext_exceptions.ManifestError):
            primary_text = "Extension Manifest Error"
            secondary_text = f"There's an error in the extension manifest:\n\n{error_message}"
        elif isinstance(error, ext_exceptions.CompatibilityError):
            primary_text = "Version Incompatibility"
            secondary_text = (
                f"Version incompatibility error:\n{error_message}\n\n"
                "Please make sure that the URL you have entered is for a Ulauncher extension, "
                "and that you are running the latest version of Ulauncher."
            )
        elif isinstance(error, ext_exceptions.NetworkError):
            primary_text = "Network Error"
            if operation == "update":
                secondary_text = (
                    f"A network error occurred while updating: {error_message}\n\n"
                    "Please check that your network is ok, that the repository is still accessible, "
                    "and that the extension repository has all the required files.\n\n"
                    f"You can also install extensions manually by adding them to {paths.USER_EXTENSIONS}."
                )
            else:
                secondary_text = (
                    f"A network error occurred: {error_message}\n\n"
                    "Please check that your network is ok, that the repository is not private, "
                    "and that the extension has all the required files.\n\n"
                    f"You can also install extensions manually by adding them to {paths.USER_EXTENSIONS}."
                )
        elif isinstance(error, ext_exceptions.DependencyError):
            updating = operation == "update"
            primary_text = f"Dependency {'Update' if updating else 'Installation'} Failed"
            secondary_text = (
                f"Failed to {'update' if updating else 'install'} extension dependencies:\n\n{error_message}\n\n"
                "If nothing seems clearly wrong on your end, consider contacting the extension "
                "author and let them know about this problem."
            )
        elif isinstance(error, ext_exceptions.ExtensionError):
            # Last of the extension errors, since every case above subclasses it. These are
            # explained failures, so the message stands on its own and asking for a bug report
            # would be wrong. Only a non-extension error is genuinely unexpected.
            primary_text = f"{operation.title()} Failed"
            secondary_text = error_message
        else:
            primary_text = f"{operation.title()} Failed"
            secondary_text = (
                "An unexpected error occurred.\n\n"
                "Please copy the technical details and report this problem via GitHub issues:\n"
                "https://github.com/Ulauncher/Ulauncher/issues\n\n"
                f"Technical details:\n{error_type}: {error_message}"
            )
            if url.startswith("http"):
                secondary_text += f"\n\nYou can also let the extension author know about this problem at: {url}"

        # Create and show error dialog
        self.dialog_launcher.show_error(primary_text, secondary_text)
