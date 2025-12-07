from __future__ import annotations

import asyncio
import logging
import threading
from typing import Callable

from gi.repository import GLib, Gtk

from ulauncher import paths
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.modes.extensions.extension_dependencies import ExtensionDependenciesRecoverableError
from ulauncher.modes.extensions.extension_manifest import ExtensionIncompatibleRecoverableError, ExtensionManifestError
from ulauncher.modes.extensions.extension_remote import ExtensionNetworkError, InvalidExtensionRecoverableError
from ulauncher.ui.windows.preferences.views import DialogLauncher, styled

logger = logging.getLogger()


class ExtensionHandlers:
    """Handles extension operations like install, remove, toggle, update, etc."""

    def __init__(self, window: Gtk.Window) -> None:
        self.window = window
        self.dialog_launcher = DialogLauncher(self.window)

    def _show_progress_dialog(self, title: str, message: str) -> Gtk.Dialog:
        """Create a progress dialog with a spinning icon"""
        dialog = styled(
            Gtk.Dialog(title=title, transient_for=self.window, modal=True, resizable=False), "progress-dialog"
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

    def add_extension(self, callback: Callable[[ExtensionController], None]) -> None:
        """Handle add extension button click"""
        dialog = Gtk.Dialog(title="Add Extension", transient_for=self.window, modal=True)
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

    def install_extension(self, url: str, callback: Callable[[ExtensionController], None]) -> None:
        """Install extension from URL"""
        progress_dialog = self._show_progress_dialog(
            "Installing extension...", "Please wait while the extension is being installed."
        )
        progress_dialog.show()

        def install_async() -> None:
            try:
                ext = asyncio.run(ExtensionController.install(url))
                asyncio.run(ext.stop())
                asyncio.run(ext.start())

                # Update UI in main thread
                def update_ui() -> None:
                    progress_dialog.destroy()
                    callback(ext)

                GLib.idle_add(update_ui)

            except Exception as error:  # noqa: BLE001

                def show_error(error: Exception) -> None:
                    progress_dialog.destroy()
                    self._show_extension_operation_error(error, url, "install")

                GLib.idle_add(show_error, error)

        # Run installation in background thread
        thread = threading.Thread(target=install_async)
        thread.daemon = True
        thread.start()

    def toggle_extension(self, state: bool, ext: ExtensionController) -> None:
        """Handle extension enable/disable toggle"""

        def toggle_async() -> None:
            try:
                asyncio.run(ext.toggle_enabled(state))

            except Exception:  # noqa: BLE001
                failed_action = "enable" if state else "disable"
                error_msg = f"Failed to {failed_action} extension"
                GLib.idle_add(self.dialog_launcher.show_error, error_msg, "Toggle operation failed")

        thread = threading.Thread(target=toggle_async)
        thread.daemon = True
        thread.start()

    def remove_extension(self, ext: ExtensionController, callback: Callable[[], None]) -> None:
        """Handle extension removal"""
        text = f'Remove extension "{ext.manifest.name}"?'
        secondary_text = "This action cannot be undone."
        response = self.dialog_launcher.show_question(text, secondary_text)

        if response == Gtk.ResponseType.YES:
            progress_dialog = self._show_progress_dialog(
                "Removing extension...", "Please wait while the extension is being removed."
            )
            progress_dialog.show()

            def remove_async() -> None:
                try:
                    asyncio.run(ext.remove())

                    def update_ui() -> None:
                        progress_dialog.destroy()
                        callback()

                    GLib.idle_add(update_ui)

                except Exception:  # noqa: BLE001
                    progress_dialog.destroy()
                    GLib.idle_add(
                        self.dialog_launcher.show_error, "Failed to remove extension", "Remove operation failed"
                    )

            thread = threading.Thread(target=remove_async)
            thread.daemon = True
            thread.start()

    def check_updates(self, ext: ExtensionController, callback: Callable[[], None]) -> None:
        """Handle checking for extension updates"""

        def check_async() -> None:
            try:
                has_update, commit_hash = asyncio.run(ext.check_update())

                def update_ui() -> None:
                    if has_update:
                        self._show_update_dialog(ext, commit_hash, callback)
                    else:
                        callback()
                        self.dialog_launcher.show(
                            f"No updates available for {ext.manifest.name}", "The extension is up to date."
                        )

                GLib.idle_add(update_ui)

            except Exception as e:  # noqa: BLE001
                callback()
                GLib.idle_add(self.dialog_launcher.show_error, "Failed to check for updates", f"Error: {e!s}")

        thread = threading.Thread(target=check_async)
        thread.daemon = True
        thread.start()

    def update_extension(self, ext: ExtensionController, callback: Callable[[], None]) -> None:
        """Update the extension"""
        # Create progress dialog with spinner
        progress_dialog = self._show_progress_dialog(
            "Updating extension...", "Please wait while the extension is being updated."
        )
        progress_dialog.show()

        def update_async() -> None:
            try:
                asyncio.run(ext.update())

                def update_ui() -> None:
                    callback()
                    progress_dialog.destroy()
                    # Show success message
                    self.dialog_launcher.show(
                        "Extension updated successfully", f"{ext.manifest.name} has been updated."
                    )

                GLib.idle_add(update_ui)

            except Exception as e:  # noqa: BLE001
                callback()

                def show_error(error: Exception) -> None:
                    url = ext.state.url
                    progress_dialog.destroy()
                    self._show_extension_operation_error(error, url, "update")

                GLib.idle_add(show_error, e)

        thread = threading.Thread(target=update_async)
        thread.daemon = True
        thread.start()

    def _show_update_dialog(self, ext: ExtensionController, commit_hash: str, callback: Callable[[], None]) -> None:
        """Show dialog when update is available"""
        text = f"Update available for '{ext.manifest.name}'"
        secondary_text = f"New version: {commit_hash[:7]}\n\nDo you want to update now?"
        response = self.dialog_launcher.show_question(text, secondary_text)
        if response == Gtk.ResponseType.YES:
            self.update_extension(ext, callback)

    def _show_extension_operation_error(self, error: Exception, url: str, operation: str = "install") -> None:
        """Show detailed error dialog for extension operation failures"""
        error_type = type(error).__name__
        error_message = str(error)

        # Extract repository URL for issue links (remove .git suffix if present)
        repo_url = url.rstrip(".git") if url.startswith("http") else None

        # Determine primary and secondary text based on error type
        if isinstance(error, InvalidExtensionRecoverableError):
            primary_text = "Invalid Extension URL"
            secondary_text = (
                "The URL should be a HTTPS git repository link or a path to a local git repository.\n\n"
                "Examples:\n"
                "• https://github.com/user/repo.git\n"
                "• https://codeberg.org/user/repo.git"
            )
        elif isinstance(error, ExtensionManifestError):
            primary_text = "Extension Manifest Error"
            secondary_text = f"There's an error in the extension manifest:\n\n{error_message}"
        elif isinstance(error, ExtensionIncompatibleRecoverableError):
            primary_text = "Version Incompatibility"
            secondary_text = (
                f"Version incompatibility error:\n{error_message}\n\n"
                "Please make sure that the URL you have entered is for a Ulauncher extension, "
                "and that you are running the latest version of Ulauncher."
            )
        elif isinstance(error, ExtensionNetworkError):
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
        elif isinstance(error, ExtensionDependenciesRecoverableError):
            if operation == "update":
                primary_text = "Dependency Update Failed"
                secondary_text = (
                    f"Failed to update extension dependencies:\n\n{error_message}\n\n"
                    "If nothing seems clearly wrong on your end, consider contacting the extension "
                    "author and let them know about this problem."
                )
            else:
                primary_text = "Dependency Installation Failed"
                secondary_text = (
                    f"Failed to install extension dependencies:\n\n{error_message}\n\n"
                    "If nothing seems clearly wrong on your end, consider contacting the extension "
                    "author and let them know about this problem."
                )
            if repo_url:
                secondary_text += f"\n\nYou can report this issue at: {repo_url}/issues"
        else:
            primary_text = f"{operation.title()} Failed"
            secondary_text = (
                "An unexpected error occurred.\n\n"
                "Please copy the technical details and report this problem via Github issues:\n"
                "https://github.com/Ulauncher/Ulauncher/issues\n\n"
                f"Technical details:\n{error_type}: {error_message}"
            )
            if repo_url:
                secondary_text += (
                    f"\n\nYou can also let the extension author know about this problem at: {repo_url}/issues"
                )

        # Create and show error dialog
        self.dialog_launcher.show_error(primary_text, secondary_text)
