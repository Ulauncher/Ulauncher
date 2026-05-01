from __future__ import annotations

import contextlib
import logging
from os.path import basename

from ulauncher.gi import GioUnix
from ulauncher.internals.result import Result
from ulauncher.modes.apps.app_history import app_history

logger = logging.getLogger()


class AppResult(Result):
    searchable = True
    app_id = ""
    _executable = ""
    actions = {"launch": {"name": "Launch application", "icon": "system-run"}}

    def __init__(self, app_info: GioUnix.DesktopAppInfo) -> None:
        super().__init__(
            name=app_info.get_display_name(),
            icon=app_info.get_string("Icon") or "",
            description=app_info.get_description() or app_info.get_generic_name() or "",
            keywords=app_info.get_keywords(),
            app_id=app_info.get_id(),
            # TryExec is what we actually want (name of/path to exec), but it's often not specified
            # get_executable uses Exec, which is always specified, but it will return the actual executable.
            # Sometimes the actual executable is not the app to start, but a wrappers like "env" or "sh -c"
            _executable=basename(app_info.get_string("TryExec") or app_info.get_executable() or ""),
        )

    @staticmethod
    def from_id(app_id: str) -> AppResult | None:
        # Suppress errors due to app being uninstalled/not found
        with contextlib.suppress(TypeError):
            if app_info := GioUnix.DesktopAppInfo.new(app_id):
                return AppResult(app_info)
        return None

    def get_searchable_fields(self) -> list[tuple[str, float]]:
        frequency_weight = 1.0
        sorted_app_ids = app_history.get_top_app_ids()
        if count := len(sorted_app_ids):
            index = sorted_app_ids.index(self.app_id) if self.app_id in sorted_app_ids else count
            frequency_weight = 1.0 - (index / count * 0.1) + 0.05

        return [
            (self.name, 1 * frequency_weight),
            (self._executable, 0.8 * frequency_weight),  # command names, such as "baobab" or "nautilus"
            (self.description, 0.7 * frequency_weight),
            *[(k, 0.6 * frequency_weight) for k in self.keywords],
        ]
