from time import time
from pathlib import Path
from ulauncher.config import PATHS
from ulauncher.utils.fold_user_path import fold_user_path
from ulauncher.utils.json_data import JsonData, json_data_class


@json_data_class
class Shortcut(JsonData):
    name = ""
    keyword = ""
    cmd = ""
    icon = ""
    is_default_search = True
    run_without_argument = False
    added = 0.0
    id = ""


class ShortcutsDb(JsonData):
    # Coerce all values to Shortcuts instead of dict and fold the icon path
    def __setitem__(self, key, value):
        if hasattr(value, "icon"):
            value.icon = fold_user_path(value.icon)
        super().__setitem__(key, Shortcut(value))

    @classmethod
    def load(cls):
        file_path = Path(f"{PATHS.CONFIG}/shortcuts.json")
        instance = cls.new_from_file(file_path)
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
            instance.save({keyword.id: keyword for keyword in keywords})

        return instance
