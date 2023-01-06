import os
from pathlib import Path
from typing import List
from gi.repository import Gdk
from ulauncher.utils.fuzzy_search import get_score
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.file_browser.FileBrowserResult import FileBrowserResult


class FileBrowserMode(BaseMode):
    LIMIT = 50

    def is_enabled(self, query: str) -> bool:
        """
        Enabled for queries like:
        ~/Downloads
        $USER/Downloads
        /usr/bin/foo
        """
        return f"{query.lstrip()} "[0] in ("~", "/", "$")

    def list_files(self, path_str: str, sort_by_atime: bool = False) -> List[str]:
        paths = sorted(
            os.scandir(path_str),
            reverse=sort_by_atime,
            key=lambda p: p.stat().st_atime if sort_by_atime else p.name.lower(),
        )
        paths.sort(key=lambda p: p.is_file())
        return [p.name for p in paths]

    def filter_dot_files(self, file_list: List[str]) -> List[str]:
        return [f for f in file_list if not f.startswith(".")]

    def handle_query(self, query: str) -> List[FileBrowserResult]:
        try:
            path = Path(os.path.expandvars(query.strip())).expanduser()
            results = []

            closest_parent = str(next(parent for parent in [path] + list(path.parents) if parent.exists()))
            remainder = "/".join(path.parts[closest_parent.count("/") + 1 :])

            if closest_parent == ".":
                raise RuntimeError(f'Invalid path "{path}"')

            if not remainder:
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
                filtered_files = list(filter(lambda fn: get_score(query, fn) > 40, sorted_files))[: self.LIMIT]
                results = [FileBrowserResult(os.path.join(closest_parent, name)) for name in filtered_files]

        except (RuntimeError, OSError):
            results = []

        return results

    def handle_key_press_event(self, widget, event, query):
        keyval = event.get_keyval()
        keyname = Gdk.keyval_name(keyval[1])
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        if (
            keyname == "BackSpace"
            and not ctrl
            and "/" in query
            and len(query.strip().rstrip("/")) > 1
            and widget.get_position() == len(query)
            and not widget.get_selection_bounds()
        ):
            # stop key press event if:
            # it's a BackSpace key and
            # Ctrl modifier is not pressed and
            # cursor is at the last position and
            # path exists and it's a directory and
            # input text is not selected
            widget.emit_stop_by_name("key-press-event")
            return SetUserQueryAction(os.path.join(Path(query).parent, ""))

        return DoNothingAction()
