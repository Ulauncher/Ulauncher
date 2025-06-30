from __future__ import annotations

import logging
import os
from os.path import basename, dirname, expandvars, isdir, join
from pathlib import Path

from ulauncher.internals import actions
from ulauncher.internals.query import Query
from ulauncher.internals.result import ActionMetadata, Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.file_browser.results import CopyPath, FileBrowserResult, OpenFolder
from ulauncher.utils.fold_user_path import fold_user_path

logger = logging.getLogger()


class FileBrowserMode(BaseMode):
    LIMIT = 50
    THRESHOLD = 40

    def parse_query_str(self, query_str: str) -> Query | None:
        """
        Enabled for queries like:
        ~/Downloads
        $USER/Downloads
        /usr/bin/foo
        """
        if f"{query_str.lstrip()} "[0] in ("~", "/", "$"):
            return Query(None, query_str)
        return None

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

    def handle_query(self, query: Query) -> list[FileBrowserResult]:
        try:
            path_str = query.argument
            if not path_str:
                return []
            path = Path(expandvars(path_str.strip())).expanduser()
            results = []

            closest_parent = str(next(parent for parent in [path, *list(path.parents)] if parent.exists()))
            remainder = "/".join(path.parts[closest_parent.count("/") + 1 :])

            if closest_parent == ".":  # invalid path
                pass

            elif not remainder:
                file_names = self.list_files(str(path), sort_by_atime=True)
                for name in self.filter_dot_files(file_names)[: self.LIMIT]:
                    file = join(closest_parent, name)
                    results.append(FileBrowserResult(file))

            else:
                file_names = self.list_files(closest_parent)
                path_str = remainder

                if not path_str.startswith("."):
                    file_names = self.filter_dot_files(file_names)

                from ulauncher.utils.fuzzy_search import get_score

                sorted_files = sorted(file_names, key=lambda fn: get_score(path_str, fn), reverse=True)
                filtered = list(filter(lambda fn: get_score(path_str, fn) > self.THRESHOLD, sorted_files))[: self.LIMIT]
                results = [FileBrowserResult(join(closest_parent, name)) for name in filtered]

        except (RuntimeError, OSError):
            results = []

        return results

    def handle_backspace(self, query_str: str) -> Query | None:
        if "/" in query_str and len(query_str.strip().rstrip("/")) > 1:
            return Query(None, join(Path(query_str).parent, ""))
        return None

    def activate_result(self, result: Result, _query: Query, alt: bool) -> ActionMetadata:
        if isinstance(result, CopyPath):
            return actions.copy(result.path)
        if isinstance(result, OpenFolder):
            return actions.open(result.path)
        if isinstance(result, FileBrowserResult):
            if not alt:
                if isdir(result.path):
                    return join(fold_user_path(result.path), "")

                return actions.open(result.path)
            if isdir(result.path):
                open_folder = OpenFolder(name=f'Open Folder "{basename(result.path)}"', path=result.path)
            else:
                open_folder = OpenFolder(name="Open Containing Folder", path=dirname(result.path))
            return [open_folder, CopyPath(path=result.path)]
        logger.error("Unexpected File Browser Mode result type '%s'", result)
        return True
