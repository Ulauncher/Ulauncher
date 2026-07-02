from __future__ import annotations

import json
import logging
import signal
from typing import TYPE_CHECKING, Any, Literal, cast
from weakref import WeakValueDictionary

import gi
from gi.repository import Gdk, Gtk

import ulauncher
from ulauncher import app_id, first_run, paths
from ulauncher.core import UlauncherCore
from ulauncher.gi import Gio, GLib
from ulauncher.internals.results_update import ResultsUpdate
from ulauncher.ui.ulauncher_window import UlauncherWindow
from ulauncher.utils import scheduling
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.settings import Settings

if TYPE_CHECKING:
    from ulauncher.internals.result import Result

logger = logging.getLogger(__name__)
events = EventBus("app")


class UlauncherApp(Gtk.Application):
    # Gtk.Applications check if the app is already registered and if so,
    # new instances sends the signals to the registered one
    # So all methods except __init__ runs on the main app
    query = ""
    # One-shot: set to True to make the next activation a no-op.
    skip_next_activate: bool = False
    # Whether the app should keep running with no windows open. Set in setup() from the
    # systemd unit state (or keep_alive fallback) and kept in sync by toggle_hold().
    _persistent: bool = False
    # App-scoped query/mode controller, shared by every launcher window.
    core: UlauncherCore
    windows: WeakValueDictionary[Literal["main", "preferences"], Gtk.ApplicationWindow] = WeakValueDictionary()
    _tray_icon: ulauncher.ui.helpers.tray_icon.TrayIcon | None = None  # pyrefly: ignore[implicit-import]

    @staticmethod
    def get_gtk_version() -> tuple[int, int, int]:
        return (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())

    @staticmethod
    def get_pygobject_version() -> tuple[int, int, int]:
        return gi.version_info  # type: ignore[attr-defined]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.update(application_id=app_id)
        super().__init__(*args, **kwargs)
        events.set_self(self)
        self.connect("startup", lambda *_: self.setup())  # runs only once on the main instance

    @events.on
    def set_query(self, value: str, update_input: bool = True) -> None:
        self.query = value.lstrip()
        if update_input and (main_window := self.windows.get("main")) and isinstance(main_window, UlauncherWindow):
            main_window.set_input(self.query)

    @events.on
    def query_changed(self, query_str: str) -> None:
        """Run the new query string through the core and render the results."""
        self.query = query_str.lstrip()
        self.core.set_query(self.query, self.show_results)

    @events.on
    def activate_result(self, result: Result, alt: bool) -> None:
        self.core.activate_result(result, self.show_results, alt)

    def handle_backspace(self, query_str: str) -> bool:
        """Whether a mode consumed the backspace by rewriting the query (smart backspace)."""
        return self.core.handle_backspace(query_str)

    @events.on
    def window_ready(self) -> None:
        # The window decides when this runs, to control startup performance.
        self.core.load_triggers(force=True)
        self.core.set_query(self.query, self.show_results)

    @events.on
    def reload_query(self) -> None:
        if "main" in self.windows:
            self.core.set_query(self.query, self.show_results)

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        Gio.ActionMap.add_action_entries(
            self,
            [
                ("show-preferences", lambda *_: self.show_preferences(), None),
                ("show-window", lambda *_: self.show_launcher(), None),
                ("hide-window", lambda *_: self.close_launcher(), None),
                ("toggle-window", lambda *_: self.toggle_window(), None),
                ("toggle-tray-icon", lambda *args: self.toggle_tray_icon(args[1].get_boolean()), "b"),
                ("set-query", lambda *args: self.activate_query(args[1].get_string()), "s"),
                ("trigger-event", lambda *args: self.delegate_custom_message(args[1].get_string()), "s"),
            ],
        )
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self._on_sigterm)

    def _on_sigterm(self) -> bool:
        self.quit()
        return False

    def do_activate(self, *_args: Any, **_kwargs: Any) -> None:
        if self.skip_next_activate:
            self.skip_next_activate = False
            return
        logger.debug("Activated via gapplication")
        self.show_launcher()

    def start(self, *, activate: bool = True) -> None:
        self.register()
        if self.get_is_remote() and not activate:
            # Daemon already running in another process; this invocation has nothing to do.
            return
        self.skip_next_activate = not activate
        self.run([])

    def setup(self) -> None:
        settings = Settings.load()
        self.core = UlauncherCore()
        # Always hold on app start (conditionally release after closing window)
        self.hold()
        self._persistent = settings.is_persistent()
        if self._persistent:
            # Sync additional hold with user settings
            self.hold()

            # Warm the modes so extension handlers register and enabled extensions start.
            # Skip if a window exists - it needs to control when this runs for startup performance reasons.
            def _warm_triggers() -> None:
                if "main" not in self.windows:
                    self.core.load_triggers()

            scheduling.run_when_idle(_warm_triggers)

        if settings.show_tray_icon and self._persistent:
            self.toggle_tray_icon(True)

        if first_run or settings.hotkey_show_app:
            from ulauncher.ui.helpers.hotkey_controller import HotkeyController

            if HotkeyController.is_supported():
                hotkey = "<Primary>space"
                if settings.hotkey_show_app and not HotkeyController.is_plasma():
                    hotkey = settings.hotkey_show_app
                if HotkeyController.setup_default(hotkey):
                    display_name = Gtk.accelerator_get_label(*Gtk.accelerator_parse(hotkey))
                    body = f'Ulauncher has added a global keyboard shortcut: "{display_name}" to your desktop settings'
                    self.show_notification("de_hotkey_auto_created", "Global shortcut created", body)
            else:
                body = (
                    "Ulauncher doesn't support setting global keyboard shortcuts for your desktop. "
                    "There are more details on this in the preferences view (click here to open)."
                )
                self.show_notification(
                    "de_hotkey_unsupported", "Cannot create global shortcut", body, "app.show-preferences"
                )

            # Remove json file setting so the notification won't show again
            settings.save(hotkey_show_app="")

    @events.on
    def show_notification(self, notification_id: str | None, title: str, body: str, default_action: str = "-") -> None:
        notification = Gio.Notification.new(title)
        # Defaults to non-existing action "-" to prevent activating on click
        notification.set_default_action(default_action)
        notification.set_body(body)
        notification.set_priority(Gio.NotificationPriority.URGENT)
        self.send_notification(notification_id, notification)

    @events.on
    def clipboard_store(self, data: str) -> None:
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(data, -1)
        clipboard.store()

    @events.on
    def copy_and_close(self, data: str) -> None:
        self.clipboard_store(data)
        self.close_launcher()

    @events.on
    def show_launcher(self) -> None:
        if (main_window := self.windows.get("main")) and main_window.get_window() is None:
            logger.warning("Ignoring stale main window reference")
            del self.windows["main"]

        if "main" not in self.windows:
            main_window = UlauncherWindow(application=self)
            main_window.connect("destroy", self._on_window_destroyed, "main")
            self.windows["main"] = main_window

    def _on_window_destroyed(self, _window: Gtk.Window, key: Literal["main", "preferences"]) -> None:
        self.windows.pop(key, None)
        if not self.windows and not self._persistent:
            # Clipboard contents only live as long as the owning app, and clipboard managers
            # (klipper, gpaste, wl-clip-persist, ...) need time to snapshot them after we set
            # ownership. X11/Wayland have no "snapshot done" event, and managers react on their
            # own schedule with non-trivial wakeup latency. GTK4's Gdk.Clipboard.store_async
            # closes this gap properly, but we're using GTK3. So delay the quit by 1s on the
            # chance the user's last action was a clipboard copy. 0.25s wasn't enough; 1s seems
            # to work, but maybe not on all systems.
            #
            # re-check windows in case the user re-opened it during the delay
            scheduling.timer(1, lambda: self.quit() if not self.windows else None)

    def show_results(self, update: ResultsUpdate) -> None:
        """Render results in the launcher window if it is currently open."""
        if main_window := cast("UlauncherWindow | None", self.windows.get("main")):
            main_window.show_results(update)

    @events.on
    def close_launcher(self) -> None:
        if main_window := self.windows.get("main"):
            main_window.close()

    @events.on
    def show_preferences(self, page: str | None = None) -> None:
        # It's technically possible to trigger this GAction before the app has started,
        # in which case we would either have to start all the modes + extensions just for the preferences.
        if not self._persistent and not self.windows:
            logger.error("You have to start Ulauncher before you can open preferences.")
            self.quit()
            return

        # Register prefs in self.windows before closing main, so the main destroy handler
        # sees a remaining window and doesn't quit the app on non-persistent setups.
        from ulauncher.ui.preferences.preferences_window import PreferencesWindow

        preferences = cast("PreferencesWindow | None", self.windows.get("preferences"))
        if preferences and preferences.get_window() is None:
            logger.warning("Ignoring stale Preferences window reference (suspecting a memory leak)")
            del self.windows["preferences"]
            preferences = None
        is_new = preferences is None
        if preferences is None:
            preferences = PreferencesWindow(application=self)
            preferences.connect("destroy", self._on_window_destroyed, "preferences")
            self.windows["preferences"] = preferences

        if main_window := self.windows.get("main"):
            cast("UlauncherWindow", main_window).close(save_query=True)

        if is_new:
            preferences.show(page)
        else:
            preferences.present(page)

    def activate_query(self, query_str: str) -> None:
        self.activate()
        self.set_query(query_str)

    def toggle_window(self) -> None:
        """Toggle window visibility - for explicit toggle requests only."""
        if "main" in self.windows:
            self.close_launcher()
        else:
            self.show_launcher()

    def delegate_custom_message(self, json_message: str) -> None:
        """Parses and delegates custom JSON messages to the EventBus listener (if any)"""
        try:
            if (data := json.loads(json_message)) and isinstance(data, dict):
                name = data.get("name")
                args = data.get("args")
                if isinstance(name, str) and isinstance(args, list):
                    events.emit(name, *args)
                    return
            logger.error("Custom message fields 'name' or 'args' are missing or invalid: %s", json_message)
        except json.JSONDecodeError:
            logger.exception("Failed to parse custom message as JSON: %s", json_message)

    @events.on
    def toggle_tray_icon(self, enable: bool) -> None:
        if not self._tray_icon:
            from ulauncher.ui.helpers.tray_icon import TrayIcon

            self._tray_icon = TrayIcon()
        # A tray icon is only meaningful while the app keeps running in the background.
        self._tray_icon.switch(enable and self._persistent)

    @events.on
    def toggle_hold(self, value: bool) -> None:
        # Idempotent: gio's release() logs a critical warning on underflow.
        if value != self._persistent:
            self._persistent = value
            self.hold() if value else self.release()
            self.toggle_tray_icon(Settings.load().show_tray_icon)

    def _cleanup(self) -> None:
        import os
        import time
        from contextlib import suppress
        from shutil import rmtree

        # Prune staging entries, except recent entries (within 1h) since they could be ongoing installs via the cli
        threshold = time.time() - 3600
        with suppress(OSError):
            for e in os.scandir(paths.EXTENSIONS_STAGING):
                with suppress(OSError):
                    if e.stat(follow_symlinks=False).st_mtime > threshold:
                        continue
                    if e.is_dir(follow_symlinks=False):
                        rmtree(e.path, ignore_errors=True)
                    else:
                        os.unlink(e.path)

    @events.on
    def quit(self) -> None:
        self._cleanup()
        super().quit()
