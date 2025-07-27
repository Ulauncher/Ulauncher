from __future__ import annotations

import contextlib
import json
import logging
import weakref
from typing import Any, cast

from gi.repository import Gio, Gtk

import ulauncher
from ulauncher import app_id, first_run
from ulauncher.cli import get_cli_args
from ulauncher.ui.windows.preferences_window import PreferencesWindow
from ulauncher.ui.windows.ulauncher_window import UlauncherWindow
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.settings import Settings
from ulauncher.utils.singleton import get_instance

logger = logging.getLogger()
events = EventBus("app")

cli_args = get_cli_args()


class UlauncherApp(Gtk.Application):
    # Gtk.Applications check if the app is already registered and if so,
    # new instances sends the signals to the registered one
    # So all methods except __init__ runs on the main app
    query = ""
    _window_ref: weakref.ReferenceType[UlauncherWindow] | None = None
    _preferences: weakref.ReferenceType[PreferencesWindow] | None = None
    _tray_icon: ulauncher.ui.tray_icon.TrayIcon | None = None

    def __call__(self, *args: Any, **kwargs: Any) -> UlauncherApp:
        return cast("UlauncherApp", get_instance(super(), self, *args, **kwargs))

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.update(application_id=app_id, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        super().__init__(*args, **kwargs)
        events.set_self(self)
        self.connect("startup", lambda *_: self.setup())  # runs only once on the main instance

    @property
    def window(self) -> UlauncherWindow | None:
        """Get the current window or None if it doesn't exist."""
        if self._window_ref:
            return self._window_ref()
        return None

    @window.setter
    def window(self, value: UlauncherWindow) -> None:
        self._window_ref = weakref.ref(value)

    @events.on
    def set_query(self, value: str, update_input: bool = True) -> None:
        self.query = value.lstrip()
        if update_input:
            events.emit("window:set_input", self.query)

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        Gio.ActionMap.add_action_entries(
            self,
            [
                ("show-preferences", lambda *_: self.show_preferences(), None),
                ("toggle-tray-icon", lambda *args: self.toggle_tray_icon(args[1].get_boolean()), "b"),
                ("set-query", lambda *args: self.activate_query(args[1].get_string()), "s"),
                ("trigger-event", lambda *args: self.delegate_custom_message(args[1].get_string()), "s"),
            ],
        )

    def do_activate(self, *_args: Any, **_kwargs: Any) -> None:
        logger.debug("Activated via gapplication")
        self.show_launcher()

    def do_command_line(self, command_line: Gio.ApplicationCommandLine, *_args: Any, **_kwargs: Any) -> int:
        # command_line is the cli arguments from the process that activated the app
        # This is unlike get_cli_args(), which is the arguments from the initial call that started ulauncher
        args = command_line.get_arguments()
        # --no-window was a temporary name in the v6 beta (never released stable)
        if "--daemon" not in args and "--no-window" not in args:
            self.activate()

        return 0

    def setup(self) -> None:
        settings = Settings.load()
        if not settings.daemonless or cli_args.daemon:
            # Keep the app running even without a window
            self.hold()

            if settings.show_tray_icon:
                self.toggle_tray_icon(True)

        if first_run or settings.hotkey_show_app:
            from ulauncher.utils.hotkey_controller import HotkeyController

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

    def show_notification(self, notification_id: str | None, title: str, body: str, default_action: str = "-") -> None:
        notification = Gio.Notification.new(title)
        # Defaults to non-existing action "-" to prevent activating on click
        notification.set_default_action(default_action)
        notification.set_body(body)
        notification.set_priority(Gio.NotificationPriority.URGENT)
        self.send_notification(notification_id, notification)

    @events.on
    def show_launcher(self) -> None:
        if not self.window:
            self.window = UlauncherWindow(application=self)

    @events.on
    def hide_launcher(self) -> None:
        if self.window:
            self.window.close()

    @events.on
    def show_preferences(self, page: str | None = None) -> None:
        if self.window:
            self.window.close(save_query=True)

        if preferences := self._preferences and self._preferences():
            preferences.present(page)
        else:
            preferences = PreferencesWindow(application=self)
            self._preferences = weakref.ref(preferences)
            preferences.show(page)

    def activate_query(self, query_str: str) -> None:
        self.activate()
        self.set_query(query_str)

    def delegate_custom_message(self, json_message: str) -> None:
        """Parses and delegates custom JSON messages to the EventBus listener (if any)"""
        with contextlib.suppress(json.JSONDecodeError):
            data = json.loads(json_message)
            if isinstance(data, dict) and "name" in data:
                events.emit(data["name"], data.get("message"))
                return

        logger.error("Invalid custom JSON message format: %s", json_message)

    @events.on
    def toggle_tray_icon(self, enable: bool) -> None:
        if not self._tray_icon:
            from ulauncher.ui.tray_icon import TrayIcon

            self._tray_icon = TrayIcon()
        self._tray_icon.switch(enable)

    @events.on
    def toggle_hold(self, value: bool) -> None:
        self.hold() if value else self.release()

    @events.on
    def quit(self) -> None:
        super().quit()
