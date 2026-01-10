from __future__ import annotations

import logging
import os
from os.path import dirname, expandvars, isdir, join
from pathlib import Path
from typing import Callable

from ulauncher.internals import effects
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.file_browser.results import FileResult, FolderResult
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.fold_user_path import fold_user_path

_events = EventBus()
logger = logging.getLogger()


class FileBrowserMode(BaseMode):
    LIMIT = 50
    THRESHOLD = 40

    def matches_query_str(self, query_str: str) -> bool:
        """
        Enabled for queries like:
        ~/Downloads
        $USER/Downloads
        /usr/bin/foo
        """
        return f"{query_str.lstrip()} "[0] in ("~", "/", "$")

    def list_files(self, path_str: str, sort_by_atime: bool = False) -> list[str]:
        _paths: dict[os.DirEntry[str], float | str] = {}  # temporary dict for direntry and sort key
        for path in os.scandir(path_str):
            try:
                _paths[path] = path.stat().st_atime if sort_by_atime else path.name.lower()
            except OSError:  # ignore broken symlinks etc
                continue
        paths = sorted(
            _paths.keys(),
            reverse=sort_by_atime,
            key=lambda p: (p.is_dir(), _paths[p]),
        )
        return [p.name for p in paths]

    def filter_dot_files(self, file_list: list[str]) -> list[str]:
        return [f for f in file_list if not f.startswith(".")]

    def handle_query(self, query: Query, callback: Callable[[effects.EffectMessage | list[Result]], None]) -> None:
        results: list[Result] = []
        try:
            path_str = query.argument
            if not path_str:
                callback([])
                return
            path = Path(expandvars(path_str.strip())).expanduser()

            closest_parent = str(next(parent for parent in [path, *list(path.parents)] if parent.exists()))
            remainder = "/".join(path.parts[closest_parent.count("/") + 1 :])

            if closest_parent != ".":  # valid path
                if not remainder:
                    file_names = self.list_files(str(path), sort_by_atime=True)
                    for name in self.filter_dot_files(file_names)[: self.LIMIT]:
                        file_path = join(closest_parent, name)
                        results.append(FolderResult(file_path) if isdir(file_path) else FileResult(file_path))

                else:
                    file_names = self.list_files(closest_parent)
                    path_str = remainder

                    if not path_str.startswith("."):
                        file_names = self.filter_dot_files(file_names)

                    from ulauncher.utils.fuzzy_search import get_score

                    sorted_files = sorted(file_names, key=lambda fn: get_score(path_str, fn), reverse=True)
                    filtered = list(filter(lambda fn: get_score(path_str, fn) > self.THRESHOLD, sorted_files))[
                        : self.LIMIT
                    ]
                    for name in filtered:
                        file_path = join(closest_parent, name)
                        results.append(FolderResult(file_path) if isdir(file_path) else FileResult(file_path))

        except (RuntimeError, OSError):
            results = []

        callback(results)

    def handle_backspace(self, query_str: str) -> Query | None:
        if "/" in query_str and len(query_str.strip().rstrip("/")) > 1:
            return Query(None, join(Path(query_str).parent, ""))
        return None

    def activate_result(
        self,
        action_id: str,
        result: Result,
        _query: Query,
        callback: Callable[[effects.EffectMessage | list[Result]], None],
    ) -> None:
        if action_id == "go_to":
            callback(effects.set_query(join(fold_user_path(result.path), "")))
        elif action_id == "open":
            callback(effects.open(result.path))
        elif action_id == "open_parent":
            callback(effects.open(dirname(result.path)))
        elif action_id == "copy_path":
            _events.emit("app:clipboard_store", result.path)
            callback(effects.close_window())
        else:
            logger.error("Unexpected action '%s' for File Browser mode result '%s'", action_id, result)
            callback(effects.do_nothing())
