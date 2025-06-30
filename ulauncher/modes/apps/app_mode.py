from __future__ import annotations

import logging
from typing import Iterator

from gi.repository import Gio

from ulauncher.config import APP_ID
from ulauncher.internals.query import Query
from ulauncher.internals.result import ActionMetadata, Result
from ulauncher.modes.apps.app_result import AppResult
from ulauncher.modes.apps.launch_app import launch_app
from ulauncher.modes.base_mode import BaseMode
from ulauncher.utils.settings import Settings

logger = logging.getLogger()


class AppMode(BaseMode):
    def get_triggers(self) -> Iterator[AppResult]:
        settings = Settings.load()

        if not settings.enable_application_mode:
            return

        apps: list[Gio.DesktopAppInfo] = Gio.DesktopAppInfo.get_all()  # type: ignore[assignment]
        for app in apps:
            executable = app.get_executable()
            if not executable or not app.get_display_name():
                continue
            if not app.get_show_in() and not settings.disable_desktop_filters:
                continue
            # Make an exception for gnome-control-center, because all the very useful specific settings
            # like "Keyboard", "Wi-Fi", "Sound" etc have NoDisplay=true
            if app.get_nodisplay() and executable != "gnome-control-center":
                continue
            # Don't show Ulauncher app in own list
            if app.get_id() == f"{APP_ID}.desktop":
                continue

            yield AppResult(app)

    def activate_result(self, result: Result, _query: Query, _alt: bool) -> ActionMetadata:
        if isinstance(result, AppResult):
            result.bump_starts()
            if not launch_app(result.app_id):
                logger.error("Could not launch app %s", result.app_id)
            return False
        return True
