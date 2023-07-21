from __future__ import annotations

import os
from pathlib import Path

from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.file_browser.FileBrowserResult import FileBrowserResult
from ulauncher.utils.fuzzy_search import get_score


class FileBrowserMode(BaseMode):
    LIMIT = 50
    THRESHOLD = 40

    def is_enabled(self, query: str) -> bool:
        """
        Enabled for queries like:
        ~/Downloads
        $USER/Downloads
        /usr/bin/foo
        """
        return f"{query.lstrip()} "[0] in ("~", "/", "$")

    def list_files(self, path_str: str, sort_by_atime: bool = False) -> list[str]:
        paths = sorted(
            os.scandir(path_str),
            reverse=sort_by_atime,
            key=lambda p: p.stat().st_atime if sort_by_atime else p.name.lower(),
        )
        paths.sort(key=lambda p: p.is_file())
        return [p.name for p in paths]

    def filter_dot_files(self, file_list: list[str]) -> list[str]:
        return [f for f in file_list if not f.startswith(".")]

    def handle_query(self, query: str) -> list[FileBrowserResult]:
        try:
            path = Path(os.path.expandvars(query.strip())).expanduser()
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
                query = remainder

                if not query.startswith("."):
                    file_names = self.filter_dot_files(file_names)

                sorted_files = sorted(file_names, key=lambda fn: get_score(query, fn), reverse=True)
                filtered = list(filter(lambda fn: get_score(query, fn) > self.THRESHOLD, sorted_files))[: self.LIMIT]
                results = [FileBrowserResult(os.path.join(closest_parent, name)) for name in filtered]

        except (RuntimeError, OSError):
            results = []

        return results

    def on_query_backspace(self, query):
        if "/" in query and len(query.strip().rstrip("/")) > 1:
            return os.path.join(Path(query).parent, "")
        return None
