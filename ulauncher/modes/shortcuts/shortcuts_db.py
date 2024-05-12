from __future__ import annotations

import re
from pathlib import Path
from time import time
from typing import Any

from ulauncher.config import paths
from ulauncher.utils.fold_user_path import fold_user_path
from ulauncher.utils.json_conf import JsonConf


class Shortcut(JsonConf):
    name = ""
    keyword = ""
    cmd = ""
    icon = ""
    is_default_search = True
    run_without_argument = False
    added = 0
    id = ""

    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        # icon path has changed in v6, from /media/{google-search,stackoverflow,wikipedia}-icon.svg to /icons/*.svg
        if key == "icon":
            value = re.sub(r"/media/(.*?)-icon", "/icons/\\1", value)
        super().__setitem__(key, value)


class ShortcutsDb(JsonConf):
    # Coerce all values to Shortcuts instead of dict and fold the icon path
    def __setitem__(self, key: str, value: dict[str, Any], validate_type: bool = True) -> None:
        if "added" in value and isinstance(value.get("added"), float):
            # convert legacy float timestamps ulauncher used
            value["added"] = int(value["added"])
        if "icon" in value:
            value["icon"] = fold_user_path(value["icon"])
        super().__setitem__(key, Shortcut(value), validate_type)

    @classmethod
    def load(cls) -> ShortcutsDb:  # type: ignore[override]
        file_path = Path(f"{paths.CONFIG}/shortcuts.json")
        instance = super().load(file_path)
        if not file_path.exists():
            added = int(time())
            keywords = [
                Shortcut(
                    id="googlesearch",
                    added=added,
                    keyword="g",
                    name="Google Search",
                    cmd="https://google.com/search?q=%s",
                    icon=f"{paths.ASSETS}/icons/google-search.png",
                ),
                Shortcut(
                    id="stackoverflow",
                    added=added,
                    keyword="so",
                    name="Stack Overflow",
                    cmd="https://stackoverflow.com/search?q=%s",
                    icon=f"{paths.ASSETS}/icons/stackoverflow.svg",
                ),
                Shortcut(
                    id="wikipedia",
                    added=added,
                    keyword="wiki",
                    name="Wikipedia",
                    cmd="https://en.wikipedia.org/wiki/%s",
                    icon=f"{paths.ASSETS}/icons/wikipedia.png",
                ),
            ]
            instance.update({keyword.id: keyword for keyword in keywords})
            instance.save()

        return instance
