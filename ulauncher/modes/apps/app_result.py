from __future__ import annotations

import logging
import operator
from os.path import basename

from gi.repository import Gio

from ulauncher import paths
from ulauncher.internals.result import Result
from ulauncher.utils.json_utils import json_load, json_save

logger = logging.getLogger()
app_starts_path = f"{paths.STATE}/app_starts.json"
app_starts: dict[str, int] = json_load(app_starts_path)


class AppResult(Result):
    searchable = True
    app_id = ""
    _executable = ""

    def __init__(self, app_info: Gio.DesktopAppInfo) -> None:
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
        try:
            app_info = Gio.DesktopAppInfo.new(app_id)
            assert app_info
            return AppResult(app_info)
        except (TypeError, AssertionError):
            logger.debug("Could not load app '%s' (probably uninstalled)", app_id)
        return None

    @staticmethod
    def get_top_app_ids() -> list[str]:
        sorted_tuples = sorted(app_starts.items(), key=operator.itemgetter(1), reverse=True)
        return [*map(operator.itemgetter(0), sorted_tuples)]

    def get_searchable_fields(self) -> list[tuple[str, float]]:
        frequency_weight = 1.0
        sorted_app_ids = AppResult.get_top_app_ids()
        if count := len(sorted_app_ids):
            index = sorted_app_ids.index(self.app_id) if self.app_id in sorted_app_ids else count
            frequency_weight = 1.0 - (index / count * 0.1) + 0.05

        return [
            (self.name, 1 * frequency_weight),
            (self._executable, 0.8 * frequency_weight),  # command names, such as "baobab" or "nautilus"
            (self.description, 0.7 * frequency_weight),
            *[(k, 0.6 * frequency_weight) for k in self.keywords],
        ]

    def bump_starts(self) -> None:
        starts = app_starts.get(self.app_id, 0)
        app_starts[self.app_id] = starts + 1
        json_save(app_starts, app_starts_path)
