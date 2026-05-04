from __future__ import annotations

import logging
from typing import Callable, Iterator

from ulauncher import app_id
from ulauncher.gi import GioUnix
from ulauncher.internals import effects
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.apps.app_history import AppHistory
from ulauncher.modes.apps.app_result import AppResult
from ulauncher.modes.apps.launch_app import launch_app
from ulauncher.modes.mode import Mode
from ulauncher.utils.settings import Settings

logger = logging.getLogger()


class AppMode(Mode):
    def handle_query(self, _query: Query, callback: Callable[[effects.EffectMessage | list[Result]], None]) -> None:
        # App mode contributes search triggers but does not handle direct query-mode execution.
        callback([])

    def get_triggers(self) -> Iterator[AppResult]:
        settings = Settings.load()

        if not settings.enable_application_mode:
            return

        apps: list[GioUnix.DesktopAppInfo] = GioUnix.DesktopAppInfo.get_all()
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
            if app.get_id() == f"{app_id}.desktop":
                continue

            yield AppResult(app)

    def get_home_results(self, limit: int) -> list[AppResult]:
        """Get the top {N} apps (based on number of launches) to show when the query is empty"""
        # TODO: filter out old apps
        app_history = AppHistory.load()
        return list(filter(None, map(AppResult.from_id, app_history.get_app_ranking())))[:limit]

    def activate_result(
        self,
        action_id: str,
        result: Result,
        _query: Query,
        callback: Callable[[effects.EffectMessage | list[Result]], None],
    ) -> None:
        if action_id == "launch":
            if not isinstance(result, AppResult):
                logger.error("Expected AppResult but got %s", type(result).__name__)
                callback(effects.do_nothing())
                return
            app_history = AppHistory.load()
            app_history.bump(result.app_id)
            if not launch_app(result.app_id):
                logger.error("Could not launch app %s", result.app_id)
            callback(effects.close_window())
            return
        logger.error("Unexpected action '%s' for App mode result '%s'", action_id, result)
        callback(effects.do_nothing())
