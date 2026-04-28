from __future__ import annotations

import re
from pathlib import Path
from time import time
from typing import Any

from ulauncher import paths
from ulauncher.utils.fold_user_path import fold_user_path
from ulauncher.utils.json_conf import JsonConf, JsonKeyValueConf

INITIAL_SHORTCUTS = [
    {
        "id": "googlesearch",
        "keyword": "g",
        "name": "Google Search",
        "cmd": "https://google.com/search?q=%s",
        "icon": f"{paths.ASSETS}/icons/google-search.png",
        "is_default_search": True,
    },
    {
        "id": "stackoverflow",
        "keyword": "so",
        "name": "Stack Overflow",
        "cmd": "https://stackoverflow.com/search?q=%s",
        "icon": f"{paths.ASSETS}/icons/stackoverflow.svg",
        "is_default_search": True,
    },
    {
        "id": "wikipedia",
        "keyword": "wiki",
        "name": "Wikipedia",
        "cmd": "https://en.wikipedia.org/wiki/%s",
        "icon": f"{paths.ASSETS}/icons/wikipedia.png",
        "is_default_search": True,
    },
]


class Shortcut(JsonConf):
    name = ""
    keyword = ""
    cmd = ""
    icon = ""
    is_default_search = False
    run_without_argument = False  # Only used in ShortcutTrigger (not Result)
    added = 0
    id = ""

    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        if key == "added" and isinstance(value, float):
            # convert legacy float timestamps ulauncher used
            value = int(value)

        # icon path has changed in v6, from /media/{google-search,stackoverflow,wikipedia}-icon.svg to /icons/*.svg
        if key == "icon" and isinstance(value, str):
            value = fold_user_path(value)
            value = re.sub(r"/media/(.*?)-icon", "/icons/\\1", value)
        super().__setitem__(key, value)


class Shortcuts(JsonKeyValueConf[str, Shortcut]):
    @classmethod
    def load(cls) -> Shortcuts:  # type: ignore[override]
        file_path = Path(f"{paths.CONFIG}/shortcuts.json")
        instance = super().load(file_path)
        if not file_path.exists():
            added = int(time())
            keywords = [Shortcut(**kw, added=added) for kw in INITIAL_SHORTCUTS]
            instance.save({keyword.id: keyword for keyword in keywords})

        return instance
