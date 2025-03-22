from __future__ import annotations

import os
from pathlib import Path

from ulauncher.internals.query import Query
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.file_browser.file_browser_result import FileBrowserResult


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
            path = Path(os.path.expandvars(path_str.strip())).expanduser()
            results = []

            closest_parent = str(next(parent for parent in [path, *list(path.parents)] if parent.exists()))
            remainder = "/".join(path.parts[closest_parent.count("/") + 1 :])

            if closest_parent == ".":  # invalid path
                pass

            elif not remainder:
                file_names = self.list_files(str(path), sort_by_atime=True)
                for name in self.filter_dot_files(file_names)[: self.LIMIT]:
                    file = os.path.join(closest_parent, name)
                    results.append(FileBrowserResult(file))

            else:
                file_names = self.list_files(closest_parent)
                query = Query(None, remainder)

                if not path_str.startswith("."):
                    file_names = self.filter_dot_files(file_names)

                from ulauncher.utils.fuzzy_search import get_score

                sorted_files = sorted(file_names, key=lambda fn: get_score(path_str, fn), reverse=True)
                filtered = list(filter(lambda fn: get_score(path_str, fn) > self.THRESHOLD, sorted_files))[: self.LIMIT]
                results = [FileBrowserResult(os.path.join(closest_parent, name)) for name in filtered]

        except (RuntimeError, OSError):
            results = []

        return results

    def on_query_backspace(self, query_str: str) -> str | None:
        if "/" in query_str and len(query_str.strip().rstrip("/")) > 1:
            return os.path.join(Path(query_str).parent, "")
        return None
