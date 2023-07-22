from pathlib import Path
from time import time

from ulauncher.config import PATHS
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


class ShortcutsDb(JsonConf):
    # Coerce all values to Shortcuts instead of dict and fold the icon path
    def __setitem__(self, key, value: dict, validate_type=True):
        if "added" in value and isinstance(value.get("added"), float):
            # convert legacy float timestamps ulauncher used
            value["added"] = int(value["added"])
        if "icon" in value:
            value["icon"] = fold_user_path(value["icon"])
        super().__setitem__(key, Shortcut(value), validate_type)

    @classmethod
    def load(cls):
        file_path = Path(f"{PATHS.CONFIG}/shortcuts.json")
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
                    icon=f"{PATHS.ASSETS}/icons/google-search.png",
                ),
                Shortcut(
                    id="stackoverflow",
                    added=added,
                    keyword="so",
                    name="Stack Overflow",
                    cmd="https://stackoverflow.com/search?q=%s",
                    icon=f"{PATHS.ASSETS}/icons/stackoverflow.svg",
                ),
                Shortcut(
                    id="wikipedia",
                    added=added,
                    keyword="wiki",
                    name="Wikipedia",
                    cmd="https://en.wikipedia.org/wiki/%s",
                    icon=f"{PATHS.ASSETS}/icons/wikipedia.png",
                ),
            ]
            instance.update({keyword.id: keyword for keyword in keywords})
            instance.save()

        return instance
