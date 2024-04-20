from __future__ import annotations

import logging
import weakref
from typing import Any, cast

from gi.repository import Gio, Gtk

from ulauncher.api.shared.query import Query
from ulauncher.config import APP_ID, FIRST_RUN
from ulauncher.ui.AppIndicator import AppIndicator
from ulauncher.ui.windows.PreferencesWindow import PreferencesWindow
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.hotkey_controller import HotkeyController
from ulauncher.utils.Settings import Settings
from ulauncher.utils.singleton import get_instance

logger = logging.getLogger()
events = EventBus("app")


class UlauncherApp(Gtk.Application):
    # Gtk.Applications check if the app is already registered and if so,
    # new instances sends the signals to the registered one
    # So all methods except __init__ runs on the main app
    _query = ""
    window: UlauncherWindow | None = None
    _preferences: weakref.ReferenceType[PreferencesWindow] | None = None
    _appindicator: AppIndicator | None = None

    def __call__(cls, *args: Any, **kwargs: Any) -> UlauncherApp:
        return cast(UlauncherApp, get_instance(super(), cls, *args, **kwargs))

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.update(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        super().__init__(*args, **kwargs)
        events.set_self(self)
        self.connect("startup", lambda *_: self.setup())  # runs only once on the main instance

    @property
    def query(self) -> Query:
        return Query(self._query)

    @events.on
    def set_query(self, value: str, update_input: bool = True) -> None:
        self._query = value.lstrip()
        if update_input and self.window:
            self.window.input.set_text(self._query)
            self.window.input.set_position(-1)

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        Gio.ActionMap.add_action_entries(
            self,
            [
                ("show-preferences", lambda *_: self.show_preferences(), None),
                ("toggle-tray-icon", lambda *args: self.toggle_tray_icon(args[1].get_boolean()), "b"),
                ("set-query", lambda *args: self.activate_query(args[1].get_string()), "s"),
            ],
        )

    def do_activate(self, *_args: Any, **_kwargs: Any) -> None:
        self.show_launcher()

    def do_command_line(self, *args: Any, **_kwargs: Any) -> int:
        # We need to use "--no-window" from the unique CLI invocation here,
        # Can't use config.get_options(), because that's the daemon's initial cli arguments
        if "--no-window" not in args[0].get_arguments():
            self.activate()

        return 0

    def setup(self) -> None:
        settings = Settings.load()
        self.hold()  # Keep the app running even without a window

        if settings.show_tray_icon:
            self.toggle_tray_icon(True)

        if FIRST_RUN or settings.hotkey_show_app:
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

            settings.hotkey_show_app = ""  # Remove json file setting so the notification won't show again
            settings.save()

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
        self.window.show()

    @events.on
    def show_preferences(self, page: str | None = None) -> None:
        events.emit("window:hide", clear_input=False)

        preferences = self._preferences and self._preferences()

        if preferences:
            preferences.present(page)
        else:
            preferences = PreferencesWindow(application=self)
            self._preferences = weakref.ref(preferences)
            preferences.show(page)

    def activate_query(self, query: str) -> None:
        self.activate()
        self.set_query(query)

    @events.on
    def toggle_tray_icon(self, enable: bool) -> None:
        if not self._appindicator:
            self._appindicator = AppIndicator()
        self._appindicator.switch(enable)

    @events.on
    def quit(self) -> None:
        super().quit()
